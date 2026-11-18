# SPDX-License-Identifier: Apache-2.0
"""Garde de budget et client OpenRouter, sans réseau (ouvreur HTTP simulé)."""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from harness.client import (ApiError, BudgetExceeded, DailyLimitReached, OpenRouterClient, RequestBudget)
from harness.config import load_config

CFG = load_config()
FAKE_KEY = "sk-or-test-NOT-A-REAL-KEY-0000"


class FakeResponse:
    def __init__(self, body: dict, headers: dict | None = None):
        self._b = json.dumps(body).encode()
        self.headers = headers or {}

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def ok_body(content="Réponse finale : 1"):
    return {"id": "gen-1", "model": CFG["model"]["id"], "provider": "Nvidia",
            "choices": [{"finish_reason": "stop", "message": {"content": content, "reasoning": "…"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                      "completion_tokens_details": {"reasoning_tokens": 3}}}


def http_error(code: int, body: str, headers: dict | None = None):
    return urllib.error.HTTPError("https://openrouter.ai", code, "err", headers or {}, io.BytesIO(body.encode()))


class Budget(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.path = Path(self.d.name) / "counter.json"

    def tearDown(self):
        self.d.cleanup()

    def test_daily_limit_is_persistent(self):
        b = RequestBudget(self.path, daily_limit=3)
        self.assertEqual([b.reserve() for _ in range(3)], [1, 2, 3])
        with self.assertRaises(BudgetExceeded):
            b.reserve()
        b2 = RequestBudget(self.path, daily_limit=3)          # nouvelle session, même jour
        self.assertEqual(b2.used_today(), 3)
        with self.assertRaises(BudgetExceeded):
            b2.reserve()

    def test_session_cap(self):
        b = RequestBudget(self.path, daily_limit=50, session_limit=2)
        b.reserve()
        b.reserve()
        with self.assertRaises(BudgetExceeded):
            b.reserve()
        self.assertEqual(b.used_today(), 2)

    def test_new_day_resets(self):
        day = [dt.datetime(2026, 11, 18, 23, 59, tzinfo=dt.timezone.utc)]
        b = RequestBudget(self.path, daily_limit=1, clock=lambda: day[0])
        b.reserve()
        with self.assertRaises(BudgetExceeded):
            b.reserve()
        day[0] = dt.datetime(2026, 11, 19, 0, 1, tzinfo=dt.timezone.utc)
        self.assertEqual(b.reserve(), 1)


class Client(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.counter = Path(self.d.name) / "counter.json"
        self.env = mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": FAKE_KEY})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.d.cleanup()

    def client(self, responses, daily=50, session=None):
        calls = []

        def opener(req, timeout):
            calls.append(req)
            r = responses.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        c = OpenRouterClient(CFG, RequestBudget(self.counter, daily, session), sleep=lambda s: None, opener=opener)
        return c, calls

    def test_success_logs_model_provider_usage(self):
        c, calls = self.client([FakeResponse(ok_body(), {"X-RateLimit-Remaining": "49"})])
        r = c.chat([{"role": "user", "content": "1+0 ?"}], {"temperature": 0.6, "max_tokens": 100, "seed": 7})
        self.assertEqual(r.model, CFG["model"]["id"])
        self.assertEqual(r.provider, "Nvidia")
        self.assertEqual(r.usage["completion_tokens"], 5)
        self.assertEqual(r.attempts, 1)
        body = json.loads(calls[0].data)
        self.assertEqual(body["seed"], 7)
        self.assertNotIn(FAKE_KEY, json.dumps(r.raw) + json.dumps(r.rate_headers) + repr(r))

    def test_refuses_when_budget_exhausted(self):
        c, calls = self.client([FakeResponse(ok_body())], daily=0)
        with self.assertRaises(BudgetExceeded):
            c.chat([{"role": "user", "content": "x"}], {})
        self.assertEqual(calls, [])                           # aucune requête envoyée

    def test_retry_on_5xx_counts_each_attempt(self):
        c, calls = self.client([http_error(502, "bad gateway"), FakeResponse(ok_body())])
        r = c.chat([{"role": "user", "content": "x"}], {})
        self.assertEqual(r.attempts, 2)
        self.assertEqual(c.budget.used_today(), 2)

    def test_429_per_minute_then_success(self):
        c, _ = self.client([http_error(429, '{"error":{"message":"Rate limit exceeded: limit_rpm/20"}}',
                                       {"Retry-After": "3"}), FakeResponse(ok_body())])
        self.assertEqual(c.chat([{"role": "user", "content": "x"}], {}).attempts, 2)

    def test_429_daily_limit_stops(self):
        c, calls = self.client([http_error(429, '{"error":{"message":"Rate limit exceeded: free-models-per-day"}}'),
                                FakeResponse(ok_body())])
        with self.assertRaises(DailyLimitReached):
            c.chat([{"role": "user", "content": "x"}], {})
        self.assertEqual(len(calls), 1)

    def test_retries_are_bounded_by_budget(self):
        c, calls = self.client([http_error(503, "x")] * 10, daily=50, session=2)
        with self.assertRaises(BudgetExceeded):
            c.chat([{"role": "user", "content": "x"}], {})
        self.assertEqual(len(calls), 2)

    def test_client_error_is_not_retried(self):
        c, calls = self.client([http_error(400, "bad request"), FakeResponse(ok_body())])
        with self.assertRaises(ApiError):
            c.chat([{"role": "user", "content": "x"}], {})
        self.assertEqual(len(calls), 1)

    def test_missing_key_sends_nothing(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            c, calls = self.client([FakeResponse(ok_body())])
            with self.assertRaises(ApiError):
                c.chat([{"role": "user", "content": "x"}], {})
            self.assertEqual(calls, [])
            self.assertEqual(c.budget.used_today(), 0)


class EvalGuard(unittest.TestCase):
    def test_runner_refuses_eval_items(self):
        from harness import run_baselines
        with mock.patch.object(run_baselines.OpenRouterClient, "chat", side_effect=AssertionError("appel interdit")):
            rc = run_baselines.main(["--campaign", "guardtest", "--items", "N3-01", "--baselines", "B0",
                                     "--runs", "1", "--allow-eval", "--max-requests", "0"])
        self.assertEqual(rc, 2)                               # eval_authorized = false dans la configuration
        self.assertFalse(CFG["campaign"]["eval_authorized"])


if __name__ == "__main__":
    unittest.main()
