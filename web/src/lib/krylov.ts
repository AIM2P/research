/* Complexité de Krylov : moteur numérique et tracés.
   On intègre  dφₙ/dt = bₙ φₙ₋₁ − bₙ₊₁ φₙ₊₁  (φₙ(0) = δₙ₀, α = 1) par Runge–Kutta 4
   et l'on compare K(t) = Σ n|φₙ|² à la solution exacte de trois familles classiques :
     SL(2,ℝ)          bₙ = √(n(n−1+η))   →  K = η sinh²t ,  C = sech^η t   (η = 2h > 0)
     Heisenberg–Weyl  bₙ = √n            →  K = t²       ,  C = e^(−t²/2)
     SU(2)            bₙ = √(n(2j+1−n))  →  K = 2j sin²t ,  C = cos^(2j) t (2j entier)
   Conventions : b₀ = 0, φₙ(0) = δₙ₀, O(t) = Σ iⁿ φₙ Oₙ, C(t) = φ₀(t), (A|B) = Tr(A†B)/Tr 𝟙.
   Références : Parker et al., PRX 9, 041017 (2019) ; Caputa, Magán, Patramanis, arXiv:2109.03824. */
import type { Bi, Lang } from '../i18n';

export type Regime = 'sl2' | 'hw' | 'su2';

export interface RegimeDef {
  param: { name: string; min: number; max: number; step: number; value: number } | null;
  tmax: number;
  dt: number;
  N: (p: number) => number;
  b: (n: number, p: number) => number;
  K: (t: number, p: number) => number;
  bnTex: string;
  exTex: string;
  cTex: string;
  /** Texte court ; peut contenir du HTML simple (<sub>). */
  note: Bi;
}

export const REGIMES: Record<Regime, RegimeDef> = {
  sl2: {
    param: { name: 'η', min: 0.5, max: 2, step: 0.1, value: 1 },
    tmax: 2.6, dt: 0.001,
    N: () => 900,
    b: (n, p) => Math.sqrt(n * (n - 1 + p)),
    K: (t, p) => p * Math.sinh(t) ** 2,
    bnTex: 'b_n = \\alpha\\sqrt{n\\,(n-1+\\eta)}',
    exTex: 'K(t) = \\eta\\,\\sinh^2(\\alpha t)',
    cTex: 'C(t) = \\operatorname{sech}^{\\eta}(\\alpha t)',
    note: { fr: 'Croissance exponentielle de taux λ<sub>K</sub> = 2α (η = 2h &gt; 0) : le comportement attendu dans les systèmes chaotiques, mais pas une preuve de chaos.',
            en: 'Exponential growth at rate λ<sub>K</sub> = 2α (η = 2h &gt; 0): the behaviour expected in chaotic systems, but not proof of chaos.' },
  },
  hw: {
    param: null,
    tmax: 6, dt: 0.004,
    N: () => 220,
    b: (n) => Math.sqrt(n),
    K: (t) => t * t,
    bnTex: 'b_n = \\alpha\\sqrt{n}',
    exTex: 'K(t) = \\alpha^2 t^2',
    cTex: 'C(t) = e^{-\\alpha^2 t^2/2}',
    note: { fr: 'Croissance quadratique : l’opérateur se répand, sans emballement exponentiel.',
            en: 'Quadratic growth: the operator spreads, with no exponential runaway.' },
  },
  su2: {
    param: { name: '2j', min: 4, max: 40, step: 2, value: 20 },
    tmax: 2 * Math.PI, dt: 0.004,
    N: (p) => p + 1,
    b: (n, p) => Math.sqrt(n * (p + 1 - n)),
    K: (t, p) => p * Math.sin(t) ** 2,
    bnTex: 'b_n = \\alpha\\sqrt{n\\,(2j+1-n)}',
    exTex: 'K(t) = 2j\\,\\sin^2(\\alpha t)',
    cTex: 'C(t) = \\cos^{2j}(\\alpha t)',
    note: { fr: 'Espace de Krylov fini, de dimension 2j + 1 (2j entier) : K(t) oscille entre 0 et 2j, avec une période π/α. Ici α est une fréquence, pas un taux de croissance.',
            en: 'Finite Krylov space of dimension 2j + 1 (2j an integer): K(t) oscillates between 0 and 2j, with period π/α. Here α is a frequency, not a growth rate.' },
  },
};

export const KRYLOV_TEX = Object.values(REGIMES).flatMap((r) => [r.bnTex, r.exTex, r.cTex]);

/* ---------------------------------------------------------------------- */
/* Simulation                                                            */
/* ---------------------------------------------------------------------- */
export class KrylovSim {
  reg: Regime = 'sl2';
  p = 1;
  N = 0;
  b = new Float64Array(0);
  phi = new Float64Array(0);
  private k1 = new Float64Array(0);
  private k2 = new Float64Array(0);
  private k3 = new Float64Array(0);
  private k4 = new Float64Array(0);
  private tmp = new Float64Array(0);
  t = 0;
  step = 0;
  totalSteps = 0;
  sampleEvery = 1;
  T: number[] = [];
  KN: number[] = [];
  KE: number[] = [];
  maxErr = 0;
  normErr = 0;
  minB = Infinity;
  exact: [number, number][] = [];
  kMax = 1;
  finished = false;

  constructor(reg: Regime, p: number) { this.reset(reg, p); }

  get def(): RegimeDef { return REGIMES[this.reg]; }
  get perFrame(): number { return Math.max(1, Math.ceil(this.totalSteps / 430)); }

  reset(reg: Regime, p: number): void {
    this.reg = reg;
    this.p = p;
    const d = this.def;
    const N = (this.N = d.N(p));
    this.b = new Float64Array(N + 1);
    this.minB = Infinity;
    for (let n = 1; n < N; n++) {
      this.b[n] = d.b(n, p);
      if (this.b[n] < this.minB) this.minB = this.b[n];
    }
    this.phi = new Float64Array(N);
    this.phi[0] = 1;
    this.k1 = new Float64Array(N); this.k2 = new Float64Array(N); this.k3 = new Float64Array(N);
    this.k4 = new Float64Array(N); this.tmp = new Float64Array(N);
    this.t = 0;
    this.step = 0;
    this.totalSteps = Math.round(d.tmax / d.dt);
    this.sampleEvery = Math.max(1, Math.round(this.totalSteps / 420));
    this.T = [0]; this.KN = [0]; this.KE = [0];
    this.maxErr = 0; this.normErr = 0;
    this.exact = [];
    this.kMax = 0;
    for (let i = 0; i <= 400; i++) {
      const tt = (d.tmax * i) / 400, kk = d.K(tt, p);
      this.exact.push([tt, kk]);
      if (kk > this.kMax) this.kMax = kk;
    }
    this.finished = false;
  }

  private deriv(y: Float64Array, out: Float64Array): void {
    const b = this.b, N = this.N;
    out[0] = -b[1] * y[1];
    for (let n = 1; n < N - 1; n++) out[n] = b[n] * y[n - 1] - b[n + 1] * y[n + 1];
    out[N - 1] = b[N - 1] * y[N - 2];
  }

  private rk4(h: number): void {
    const { phi, k1, k2, k3, k4, tmp, N } = this;
    this.deriv(phi, k1);
    for (let i = 0; i < N; i++) tmp[i] = phi[i] + 0.5 * h * k1[i];
    this.deriv(tmp, k2);
    for (let i = 0; i < N; i++) tmp[i] = phi[i] + 0.5 * h * k2[i];
    this.deriv(tmp, k3);
    for (let i = 0; i < N; i++) tmp[i] = phi[i] + h * k3[i];
    this.deriv(tmp, k4);
    const c = h / 6;
    for (let i = 0; i < N; i++) phi[i] += c * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
  }

  measure(): { norm: number; K: number } {
    let s = 0, k = 0;
    for (let n = 0; n < this.N; n++) { const q = this.phi[n] * this.phi[n]; s += q; k += n * q; }
    return { norm: s, K: k };
  }

  advance(nSteps: number): void {
    const d = this.def;
    for (let i = 0; i < nSteps && this.step < this.totalSteps; i++) {
      this.rk4(d.dt);
      this.step++;
      this.t = this.step * d.dt;
      if (this.step % this.sampleEvery === 0 || this.step === this.totalSteps) {
        const m = this.measure(), ke = d.K(this.t, this.p);
        this.T.push(this.t); this.KN.push(m.K); this.KE.push(ke);
        const e = Math.abs(m.K - ke) / Math.max(1, ke);
        if (e > this.maxErr) this.maxErr = e;
        this.normErr = Math.abs(m.norm - 1);
      }
    }
    if (this.step >= this.totalSteps) this.finished = true;
  }

  get lastK(): number { return this.KN[this.KN.length - 1]; }
}

/* ---------------------------------------------------------------------- */
/* Mise en forme des nombres                                             */
/* ---------------------------------------------------------------------- */
const SUP: Record<string, string> = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
const dec = (s: string, lang: Lang) => (lang === 'fr' ? s.replace('.', ',') : s);

export function sci(x: number): string {
  if (x === 0) return '0';
  if (x >= 1e-3) return x.toPrecision(2);
  const e = Math.floor(Math.log10(x)), m = x / 10 ** e;
  return `${m.toFixed(1)} × 10${String(e).split('').map((c) => SUP[c]).join('')}`;
}
export function fmt(x: number, lang: Lang): string {
  const a = Math.abs(x);
  return dec(a >= 100 ? x.toFixed(0) : a >= 10 ? x.toFixed(1) : a >= 1 ? x.toFixed(2) : x.toFixed(3), lang);
}
const fmtSig = (x: number, lang: Lang) => dec(x >= 0.1 ? x.toFixed(2) : x.toPrecision(2), lang);
const fmtTick = (v: number, step: number, lang: Lang) => dec(v.toFixed(Math.max(0, -Math.floor(Math.log10(step) + 1e-9))), lang);
function niceStep(range: number, count: number): number {
  const raw = range / count, mag = 10 ** Math.floor(Math.log10(raw)), f = raw / mag;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
}

/* ---------------------------------------------------------------------- */
/* Tracés (canevas)                                                      */
/* ---------------------------------------------------------------------- */
const COL = {
  ink3: '#93A0C2', grid: 'rgba(174,185,214,.13)', axis: 'rgba(174,185,214,.38)',
  teal: '#1FB28C', exact: 'rgba(247,242,230,.78)', cross: 'rgba(247,242,230,.4)', navy: '#0A1430',
};
export const PAD = { l: 46, r: 12, t: 12, b: 26 };
const HEIGHT = 220;

function prep(canvas: HTMLCanvasElement) {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = canvas.clientWidth || 600, h = HEIGHT;
  if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
  }
  const ctx = canvas.getContext('2d')!;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.font = '500 11.5px "JetBrains Mono Variable", "JetBrains Mono", ui-monospace, monospace';
  return { ctx, w, h };
}

export interface WaveView { viewMax: number; yMax: number }
export interface WaveGeom { bw: number; count: number; ph: number; yMax: number }

export function drawWave(canvas: HTMLCanvasElement, sim: KrylovSim, view: WaveView, smooth: boolean, lang: Lang): WaveGeom {
  const { ctx, w, h } = prep(canvas);
  const pw = w - PAD.l - PAD.r, ph = h - PAD.t - PAD.b;
  const { phi, N } = sim;

  if (sim.reg !== 'su2') {
    let cum = 0, edge = 0;
    for (let n = 0; n < N; n++) { cum += phi[n] * phi[n]; if (cum > 1 - 1e-4) { edge = n; break; } }
    view.viewMax = Math.min(N - 1, Math.max(view.viewMax, Math.ceil(edge * 1.12), 30));
  } else view.viewMax = N - 1;

  const count = view.viewMax + 1;
  let peak = 0;
  for (let i = 0; i < count; i++) peak = Math.max(peak, phi[i] * phi[i]);
  const target = Math.max(peak * 1.15, 1e-6);
  view.yMax = !smooth || target > view.yMax ? target : view.yMax + (target - view.yMax) * 0.2;

  ctx.lineWidth = 1;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  for (const f of [0.5, 1]) {
    const y = PAD.t + ph * (1 - f) + 0.5;
    ctx.strokeStyle = COL.grid;
    ctx.beginPath(); ctx.moveTo(PAD.l, y); ctx.lineTo(w - PAD.r, y); ctx.stroke();
    ctx.fillStyle = COL.ink3;
    ctx.fillText(fmtSig(view.yMax * f, lang), PAD.l - 8, y);
  }
  ctx.strokeStyle = COL.axis;
  ctx.beginPath(); ctx.moveTo(PAD.l, PAD.t + ph + 0.5); ctx.lineTo(w - PAD.r, PAD.t + ph + 0.5); ctx.stroke();

  const bw = pw / count, gap = bw > 6 ? 2 : bw > 3 ? 1 : 0;
  ctx.fillStyle = COL.teal;
  for (let m = 0; m < count; m++) {
    const v = (phi[m] * phi[m]) / view.yMax;
    if (v <= 0) continue;
    const bh = Math.max(0.5, Math.min(1, v) * ph);
    const x = PAD.l + m * bw + gap / 2, bwid = Math.max(1, bw - gap), r = Math.min(3, bwid / 2), y = PAD.t + ph - bh;
    ctx.beginPath();
    ctx.moveTo(x, y + bh);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.lineTo(x + bwid - r, y);
    ctx.quadraticCurveTo(x + bwid, y, x + bwid, y + r);
    ctx.lineTo(x + bwid, y + bh);
    ctx.closePath();
    ctx.fill();
  }

  ctx.fillStyle = COL.ink3;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  const st = niceStep(view.viewMax, 5);
  let lastX = 0;
  for (let tick = 0; tick <= view.viewMax; tick += st) {
    lastX = PAD.l + (tick + 0.5) * bw;
    ctx.fillText(String(tick), lastX, PAD.t + ph + 7);
  }
  ctx.textAlign = 'left';
  if (w - PAD.r - lastX > 30) ctx.fillText('n', w - PAD.r - 8, PAD.t + ph + 7);

  return { bw, count, ph, yMax: view.yMax };
}

export interface KGeom { X: (t: number) => number; Y: (k: number) => number; pw: number }

export function drawK(canvas: HTMLCanvasElement, sim: KrylovSim, hoverT: number | null, lang: Lang): KGeom {
  const { ctx, w, h } = prep(canvas);
  const d = sim.def;
  const pw = w - PAD.l - PAD.r, ph = h - PAD.t - PAD.b;
  const yMax = sim.kMax * 1.08 || 1;
  const X = (tt: number) => PAD.l + (tt / d.tmax) * pw;
  const Y = (k: number) => PAD.t + ph * (1 - k / yMax);

  ctx.lineWidth = 1;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  const st = niceStep(yMax, 4);
  for (let v = st; v < yMax; v += st) {
    const y = Math.round(Y(v)) + 0.5;
    ctx.strokeStyle = COL.grid;
    ctx.beginPath(); ctx.moveTo(PAD.l, y); ctx.lineTo(w - PAD.r, y); ctx.stroke();
    ctx.fillStyle = COL.ink3;
    ctx.fillText(fmtTick(v, st, lang), PAD.l - 8, y);
  }
  ctx.strokeStyle = COL.axis;
  ctx.beginPath(); ctx.moveTo(PAD.l, PAD.t + ph + 0.5); ctx.lineTo(w - PAD.r, PAD.t + ph + 0.5); ctx.stroke();

  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  const ticks: [number, string][] = sim.reg === 'su2'
    ? [[0, '0'], [Math.PI / 2, 'π/2'], [Math.PI, 'π'], [1.5 * Math.PI, '3π/2'], [2 * Math.PI, '2π']]
    : (() => {
        const a: [number, string][] = [], s2 = niceStep(d.tmax, 5);
        for (let q = 0; q <= d.tmax + 1e-9; q += s2) a.push([q, fmtTick(q, s2, lang)]);
        return a;
      })();
  for (const [v, label] of ticks) ctx.fillText(label, X(v), PAD.t + ph + 7);
  ctx.textAlign = 'left';
  if (w - PAD.r - X(ticks[ticks.length - 1][0]) > 30) ctx.fillText('t', w - PAD.r - 6, PAD.t + ph + 7);

  // solution exacte (tirets)
  ctx.strokeStyle = COL.exact;
  ctx.lineWidth = 1.6;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  sim.exact.forEach(([tt, kk], i) => (i ? ctx.lineTo(X(tt), Y(kk)) : ctx.moveTo(X(tt), Y(kk))));
  ctx.stroke();
  ctx.setLineDash([]);

  // simulation (trait plein)
  ctx.strokeStyle = COL.teal;
  ctx.lineWidth = 2.4;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  sim.T.forEach((tt, i) => (i ? ctx.lineTo(X(tt), Y(sim.KN[i])) : ctx.moveTo(X(tt), Y(sim.KN[i]))));
  ctx.stroke();
  const lx = X(sim.T[sim.T.length - 1]), ly = Y(sim.lastK);
  ctx.fillStyle = COL.teal;
  ctx.strokeStyle = COL.navy;
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(lx, ly, 4.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();

  if (hoverT != null) {
    const hx = Math.round(X(hoverT)) + 0.5;
    ctx.strokeStyle = COL.cross;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx, PAD.t); ctx.lineTo(hx, PAD.t + ph); ctx.stroke();
  }
  return { X, Y, pw };
}
