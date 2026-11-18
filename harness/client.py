# SPDX-License-Identifier: Apache-2.0
"""Client OpenRouter (API compatible OpenAI) en bibliothèque standard, avec garde de budget.

- La clé est lue seulement dans la variable d'environnement ``OPENROUTER_API_KEY`` ; elle n'est jamais
  affichée, journalisée ni transmise aux sous-processus (Lean).
- Chaque tentative HTTP est d'abord réservée dans un compteur quotidien persistant (fichier JSON,
  verrouillé) : le client refuse d'envoyer une requête qui dépasserait le budget du jour ou le
  plafond de la session. Les tentatives échouées comptent aussi, par prudence.
- Reprises avec attente exponentielle sur erreurs réseau et 5xx ; sur 429, attente puis reprise si
  la limite est par minute, arrêt immédiat si la limite quotidienne est atteinte.
- Chaque réponse rend le modèle renvoyé, le fournisseur, l'usage (tokens), la latence, la raison
  d'arrêt et les en-têtes de limite.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows : pas de verrou de fichier (le harnais tourne sous WSL)
    fcntl = None


class BudgetExceeded(RuntimeError):
    """Le budget de requêtes (quotidien ou de session) est épuisé : aucune requête n'est envoyée."""


class DailyLimitReached(RuntimeError):
    """Le fournisseur signale que la limite quotidienne est atteinte (HTTP 429)."""


class ApiError(RuntimeError):
    def __init__(self, msg: str, status: int | None = None, attempts: int = 0):
        super().__init__(msg)
        self.status = status
        self.attempts = attempts


class RequestBudget:
    """Compteur persistant de requêtes par jour (UTC par défaut) et plafond de session."""

    def __init__(self, path: Path, daily_limit: int, session_limit: int | None = None,
                 clock=None):
        self.path = Path(path)
        self.daily_limit = int(daily_limit)
        self.session_limit = session_limit
        self.session_used = 0
        self._clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))

    def today(self) -> str:
        return self._clock().strftime("%Y-%m-%d")

    @contextlib.contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        with open(lock, "a+") as fh:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_UN)

    def _read(self) -> dict:
        if not self.path.is_file():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            raise RuntimeError(f"compteur de requêtes illisible : {self.path} (à réparer à la main)")

    def used_today(self) -> int:
        with self._locked():
            return int(self._read().get(self.today(), 0))

    def remaining(self) -> int:
        left = self.daily_limit - self.used_today()
        if self.session_limit is not None:
            left = min(left, self.session_limit - self.session_used)
        return max(0, left)

    def reserve(self) -> int:
        """Réserve une requête ; renvoie le total du jour après réservation, ou lève BudgetExceeded."""
        if self.session_limit is not None and self.session_used >= self.session_limit:
            raise BudgetExceeded(f"plafond de session atteint ({self.session_limit} requêtes)")
        with self._locked():
            data = self._read()
            day = self.today()
            used = int(data.get(day, 0))
            if used >= self.daily_limit:
                raise BudgetExceeded(f"budget quotidien atteint ({used}/{self.daily_limit} le {day}, UTC)")
            data[day] = used + 1
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
            os.replace(tmp, self.path)
        self.session_used += 1
        return used + 1


@dataclass
class ChatResult:
    content: str
    reasoning: str
    model: str | None
    provider: str | None
    usage: dict
    finish_reason: str | None
    native_finish_reason: str | None
    latency_s: float
    attempts: int
    response_id: str | None
    system_fingerprint: str | None
    rate_headers: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)


class OpenRouterClient:
    def __init__(self, cfg: dict, budget: RequestBudget, sleep=time.sleep, opener=None):
        m, h = cfg["model"], cfg["http"]
        self.endpoint = m["endpoint"]
        self.model = m["id"]
        self.app_title = m.get("app_title", "")
        self.provider = m.get("provider") or {}
        self.timeout = float(h["timeout_s"])
        self.max_retries = int(h["max_retries"])
        self.backoff_base = float(h["backoff_base_s"])
        self.backoff_max = float(h["backoff_max_s"])
        self.rate_limit_wait = float(h["rate_limit_wait_s"])
        self.budget = budget
        self._sleep = sleep
        self._open = opener or urllib.request.urlopen

    @staticmethod
    def _key() -> str:
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise ApiError("OPENROUTER_API_KEY absente de l'environnement (source ~/.aim2p_env sous WSL)")
        return key

    def body(self, messages: list[dict], params: dict) -> dict:
        b = {"model": self.model, "messages": messages}
        for k in ("temperature", "top_p", "max_tokens", "seed", "reasoning"):
            if params.get(k) is not None:
                b[k] = params[k]
        if self.provider:
            b["provider"] = self.provider
        return b

    def chat(self, messages: list[dict], params: dict) -> ChatResult:
        payload = json.dumps(self.body(messages, params)).encode("utf-8")
        key = self._key()
        attempt, last_err = 0, None
        while attempt <= self.max_retries:
            self.budget.reserve()          # lève BudgetExceeded avant tout envoi
            attempt += 1
            req = urllib.request.Request(self.endpoint, data=payload, method="POST", headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                **({"X-Title": self.app_title} if self.app_title else {}),
            })
            t0 = time.monotonic()
            try:
                with self._open(req, timeout=self.timeout) as r:
                    raw_bytes = r.read()
                    headers = {k.lower(): v for k, v in r.headers.items()}
                latency = time.monotonic() - t0
                data = json.loads(raw_bytes.decode("utf-8"))
            except urllib.error.HTTPError as e:
                text = _safe_read(e)
                headers = {k.lower(): v for k, v in (e.headers or {}).items()}
                if e.code == 429:
                    if _is_daily_limit(text, headers):
                        raise DailyLimitReached(f"HTTP 429, limite quotidienne : {text[:300]}") from None
                    wait = _retry_after(headers) or self.rate_limit_wait
                    last_err = ApiError(f"HTTP 429 : {text[:300]}", 429, attempt)
                    self._sleep(min(wait, self.backoff_max))
                    continue
                if e.code in (408, 500, 502, 503, 504, 520, 522, 524, 529):
                    last_err = ApiError(f"HTTP {e.code} : {text[:300]}", e.code, attempt)
                    self._sleep(self._backoff(attempt))
                    continue
                raise ApiError(f"HTTP {e.code} : {text[:500]}", e.code, attempt) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError, OSError) as e:
                last_err = ApiError(f"erreur réseau ou réponse illisible : {type(e).__name__}: {e}", None, attempt)
                self._sleep(self._backoff(attempt))
                continue

            if "error" in data and not data.get("choices"):
                err = data["error"] if isinstance(data["error"], dict) else {"message": str(data["error"])}
                code = err.get("code")
                msg = str(err.get("message", ""))[:300]
                if code == 429 and _is_daily_limit(msg, headers):
                    raise DailyLimitReached(f"limite quotidienne : {msg}")
                last_err = ApiError(f"erreur du fournisseur ({code}) : {msg}", code if isinstance(code, int) else None, attempt)
                self._sleep(self._backoff(attempt))
                continue
            ch = (data.get("choices") or [{}])[0]
            msg = ch.get("message") or {}
            if ch.get("finish_reason") == "error":
                last_err = ApiError(f"génération interrompue par le fournisseur : {ch.get('error')}", None, attempt)
                self._sleep(self._backoff(attempt))
                continue
            return ChatResult(
                content=msg.get("content") or "",
                reasoning=msg.get("reasoning") or "",
                model=data.get("model"),
                provider=data.get("provider"),
                usage=data.get("usage") or {},
                finish_reason=ch.get("finish_reason"),
                native_finish_reason=ch.get("native_finish_reason"),
                latency_s=round(latency, 3),
                attempts=attempt,
                response_id=data.get("id"),
                system_fingerprint=data.get("system_fingerprint"),
                rate_headers={k: v for k, v in headers.items() if k.startswith("x-ratelimit")},
                raw=data,
            )
        assert last_err is not None
        last_err.attempts = attempt
        raise last_err

    def _backoff(self, attempt: int) -> float:
        return min(self.backoff_max, self.backoff_base * 2 ** (attempt - 1))


def _safe_read(e: urllib.error.HTTPError) -> str:
    try:
        return e.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""
    finally:
        e.close()


def _retry_after(headers: dict) -> float | None:
    v = headers.get("retry-after")
    if v:
        try:
            return float(v)
        except ValueError:
            return None
    reset = headers.get("x-ratelimit-reset")
    if reset:
        try:
            ms = float(reset)
            delta = ms / 1000 - time.time()
            return max(1.0, delta) if delta < 3600 else None
        except ValueError:
            return None
    return None


def _is_daily_limit(text: str, headers: dict) -> bool:
    t = text.lower()
    if "per-day" in t or "per day" in t or "free-models-per-day" in t or "daily" in t:
        return True
    if headers.get("x-ratelimit-remaining") == "0":
        reset = headers.get("x-ratelimit-reset")
        try:
            return reset is not None and float(reset) / 1000 - time.time() > 3600
        except ValueError:
            return False
    return False
