import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react';
import { t, tx, plain, type Lang } from '../../i18n';
import {
  KrylovSim, REGIMES, PAD, drawK, drawWave, fmt, sci,
  type KGeom, type Regime, type WaveGeom, type WaveView,
} from '../../lib/krylov';

interface Props { lang: Lang; math: Record<string, string> }
interface Tip { x: number; y: number; text: string }
interface Stats { step: number; t: number; K: number; normErr: number; maxErr: number; minB: number; N: number }

const REGIME_ORDER: { id: Regime; name: string; key: 'kr.r1' | 'kr.r2' | 'kr.r3' }[] = [
  { id: 'sl2', name: 'SL(2,ℝ)', key: 'kr.r1' },
  { id: 'hw', name: 'Heisenberg–Weyl', key: 'kr.r2' },
  { id: 'su2', name: 'SU(2)', key: 'kr.r3' },
];

const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  || new URLSearchParams(window.location.search).has('static');

function snapshot(sim: KrylovSim): Stats {
  return { step: sim.step, t: sim.t, K: sim.lastK, normErr: sim.normErr, maxErr: sim.maxErr, minB: sim.minB, N: sim.N };
}

export default function KrylovLab({ lang, math }: Props) {
  const [reg, setReg] = useState<Regime>('sl2');
  const [params, setParams] = useState({ sl2: 1, su2: 20 });
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState(false);
  const p = reg === 'hw' ? 0 : params[reg];

  // Création paresseuse : une seule simulation pour toute la vie du composant.
  const simRef = useRef<KrylovSim>(null as unknown as KrylovSim);
  if (!simRef.current) simRef.current = new KrylovSim('sl2', 1);
  const [stats, setStats] = useState<Stats>(() => snapshot(simRef.current));
  const viewRef = useRef<WaveView>({ viewMax: 30, yMax: 1 });
  const waveRef = useRef<HTMLCanvasElement>(null);
  const kRef = useRef<HTMLCanvasElement>(null);
  const labRef = useRef<HTMLDivElement>(null);
  const geom = useRef<{ wave?: WaveGeom; k?: KGeom }>({});
  const raf = useRef(0);
  const runningRef = useRef(false);
  const visibleRef = useRef(false);
  const startedRef = useRef(false);
  const [tipWave, setTipWave] = useState<Tip | null>(null);
  const [tipK, setTipK] = useState<Tip | null>(null);

  const draw = useCallback((hoverT: number | null = null) => {
    const sim = simRef.current;
    if (waveRef.current) geom.current.wave = drawWave(waveRef.current, sim, viewRef.current, runningRef.current, lang);
    if (kRef.current) geom.current.k = drawK(kRef.current, sim, hoverT, lang);
  }, [lang]);

  const frame = useCallback(() => {
    raf.current = 0;
    if (!runningRef.current) return;
    const sim = simRef.current;
    sim.advance(sim.perFrame);
    draw();
    setStats(snapshot(sim));
    if (sim.finished) {
      runningRef.current = false;
      setRunning(false);
      setFinished(true);
      draw();
      return;
    }
    if (visibleRef.current) raf.current = requestAnimationFrame(frame);
  }, [draw]);

  const play = useCallback(() => {
    const sim = simRef.current;
    if (sim.finished) { sim.reset(sim.reg, sim.p); viewRef.current = { viewMax: 30, yMax: 1 }; setFinished(false); }
    startedRef.current = true;
    if (reducedMotion()) {
      sim.advance(sim.totalSteps);
      draw(); setStats(snapshot(sim)); setFinished(true);
      return;
    }
    runningRef.current = true;
    setRunning(true);
    if (!raf.current) raf.current = requestAnimationFrame(frame);
  }, [draw, frame]);

  const pause = () => { runningRef.current = false; setRunning(false); };

  // (Re)lance la simulation quand le régime ou le paramètre change.
  useEffect(() => {
    const sim = simRef.current;
    sim.reset(reg, p);
    viewRef.current = { viewMax: 30, yMax: 1 };
    setFinished(false);
    setStats(snapshot(sim));
    draw();
    if (startedRef.current) play();
  }, [reg, p, draw, play]);

  // Démarre quand le labo devient visible ; s'interrompt hors de l'écran.
  useEffect(() => {
    const el = labRef.current;
    if (!el) return;
    // Sans animation (préférence système ou ?static) : résultat final immédiat.
    if (reducedMotion() && !startedRef.current) play();
    const io = new IntersectionObserver(([entry]) => {
      visibleRef.current = entry.isIntersecting;
      if (entry.isIntersecting && !startedRef.current) play();
      else if (entry.isIntersecting && runningRef.current && !raf.current) raf.current = requestAnimationFrame(frame);
    }, { threshold: 0.25 });
    io.observe(el);
    const ro = new ResizeObserver(() => draw());
    if (waveRef.current) ro.observe(waveRef.current);
    return () => { io.disconnect(); ro.disconnect(); cancelAnimationFrame(raf.current); raf.current = 0; };
  }, [draw, frame, play]);

  /* --- Survol ---------------------------------------------------------- */
  function onWaveMove(e: MouseEvent<HTMLCanvasElement>) {
    const g = geom.current.wave;
    if (!g) return;
    const x = e.clientX - e.currentTarget.getBoundingClientRect().left;
    const n = Math.floor((x - PAD.l) / g.bw);
    if (n < 0 || n >= g.count) { setTipWave(null); return; }
    const q = simRef.current.phi[n] ** 2;
    const y = PAD.t + g.ph * (1 - Math.min(1, q / g.yMax));
    setTipWave({ x: PAD.l + (n + 0.5) * g.bw, y: Math.max(18, y), text: `n = ${n} · |φₙ|² = ${q < 1e-3 ? sci(q) : fmt(q, lang)}` });
  }
  function onKMove(e: MouseEvent<HTMLCanvasElement>) {
    const g = geom.current.k;
    if (!g) return;
    const sim = simRef.current, d = sim.def;
    const x = e.clientX - e.currentTarget.getBoundingClientRect().left;
    const tt = ((x - PAD.l) / g.pw) * d.tmax;
    if (tt < 0 || tt > d.tmax) { setTipK(null); draw(); return; }
    const exactWord = tx({ fr: 'exacte', en: 'exact' }, lang);
    const ke = d.K(tt, sim.p);
    let text = `t = ${fmt(tt, lang)} · ${exactWord} ${fmt(ke, lang)}`;
    const tLast = sim.T[sim.T.length - 1];
    if (tLast > 0 && tt <= tLast) {
      const i = Math.min(sim.T.length - 1, Math.round((tt / tLast) * (sim.T.length - 1)));
      text = `t = ${fmt(sim.T[i], lang)} · K = ${fmt(sim.KN[i], lang)} · ${exactWord} ${fmt(sim.KE[i], lang)}`;
    }
    draw(tt);
    setTipK({ x: g.X(tt), y: Math.max(18, g.Y(Math.min(sim.kMax, ke))), text });
  }

  const def = REGIMES[reg];
  const started = stats.step > 0;
  const normOk = stats.normErr < 1e-8;
  const exactOk = stats.maxErr < 1e-6;
  const param = def.param;
  const paramLabel = param ? (reg === 'su2' ? String(p) : (lang === 'fr' ? p.toFixed(1).replace('.', ',') : p.toFixed(1))) : '';

  const check = (state: 'ok' | 'fail' | 'pending') =>
    state === 'pending' ? 'is-pending' : state === 'fail' ? 'is-fail' : undefined;

  return (
    <div className="lab" ref={labRef}>
      <div className="lab-head">
        <div>
          <p className="lab-k" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.k') }} />
          <h3 dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.t') }} />
        </div>
        <div className="regimes" role="radiogroup" aria-label={plain(t(lang, 'kr.lab.regime'))}>
          {REGIME_ORDER.map((r) => (
            <button key={r.id} type="button" role="radio" className="regime" aria-checked={reg === r.id} onClick={() => setReg(r.id)}>
              <b>{r.name}</b>
              <span dangerouslySetInnerHTML={{ __html: t(lang, r.key) }} />
            </button>
          ))}
        </div>
      </div>

      <div className="lab-grid">
        <div className="lab-side">
          <div className="lab-formula">
            <p className="lab-label" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.bn') }} />
            <div className="math-block" dangerouslySetInnerHTML={{ __html: math[def.bnTex] ?? def.bnTex }} />
            <p className="lab-label" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.c') }} />
            <div className="math-block" dangerouslySetInnerHTML={{ __html: math[def.cTex] ?? def.cTex }} />
            <p className="lab-label" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.exact') }} />
            <div className="math-block" dangerouslySetInnerHTML={{ __html: math[def.exTex] ?? def.exTex }} />
            <p className="lab-regime-note" dangerouslySetInnerHTML={{ __html: tx(def.note, lang) }} />
          </div>

          <div className={'lab-param' + (param ? '' : ' is-hidden')}>
            {param && (
              <>
                <label htmlFor="lab-slider" className="lab-label">{param.name} = <output>{paramLabel}</output></label>
                <input
                  type="range" id="lab-slider" min={param.min} max={param.max} step={param.step} value={p}
                  onChange={(e) => setParams((s) => ({ ...s, [reg]: Number(e.target.value) }))}
                />
              </>
            )}
          </div>

          <div className="lab-buttons">
            <button type="button" className="btn btn-primary btn-sm" onClick={() => (running ? pause() : play())}>
              <svg className="ico"><use href={running ? '#i-pause' : '#i-play'} /></svg>
              <span>{running ? 'Pause' : finished ? tx({ fr: 'Relancer', en: 'Run again' }, lang) : tx({ fr: 'Lecture', en: 'Play' }, lang)}</span>
            </button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => { pause(); simRef.current.finished = true; play(); }}>
              <svg className="ico"><use href="#i-reset" /></svg>
              <span dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.reset') }} />
            </button>
          </div>

          <div className="verifier">
            <p className="lab-label" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.v.title') }} />
            <ul>
              <li className={check(!started ? 'pending' : normOk ? 'ok' : 'fail')}>
                <span className="chk-ico"><svg className="ico"><use href={started && !normOk ? '#i-x' : '#i-check'} /></svg></span>
                <div><b dangerouslySetInnerHTML={{ __html: t(lang, 'kr.v.norm') }} /><code>{started ? `|Σ|φₙ|² − 1| = ${sci(stats.normErr)}` : '—'}</code></div>
              </li>
              <li className={check(!started ? 'pending' : exactOk ? 'ok' : 'fail')}>
                <span className="chk-ico"><svg className="ico"><use href={started && !exactOk ? '#i-x' : '#i-check'} /></svg></span>
                <div><b dangerouslySetInnerHTML={{ __html: t(lang, 'kr.v.exact') }} /><code>{started ? `max |ΔK| / max(1, K) = ${sci(stats.maxErr)}` : '—'}</code></div>
              </li>
              <li className={check(stats.minB > 0 ? 'ok' : 'fail')}>
                <span className="chk-ico"><svg className="ico"><use href="#i-check" /></svg></span>
                <div><b dangerouslySetInnerHTML={{ __html: t(lang, 'kr.v.pos') }} /><code>{`min bₙ = ${fmt(stats.minB, lang)} > 0  (n = 1…${stats.N - 1})`}</code></div>
              </li>
            </ul>
          </div>
        </div>

        <div className="lab-plots">
          <figure className="plot">
            <figcaption>
              <span dangerouslySetInnerHTML={{ __html: t(lang, 'kr.p1') }} />
              <span className="plot-readout">{`t = ${fmt(stats.t, lang)} · K(t) = ${fmt(stats.K, lang)}`}</span>
            </figcaption>
            <div className="plot-canvas-wrap">
              <canvas ref={waveRef} height={220} role="img" aria-label={tx({ fr: 'Distribution |φn(t)|² le long de la chaîne', en: 'Distribution |φn(t)|² along the chain' }, lang)}
                onMouseMove={onWaveMove} onMouseLeave={() => setTipWave(null)} />
              {tipWave && <div className="plot-tip" style={{ left: tipWave.x, top: tipWave.y }}>{tipWave.text}</div>}
            </div>
          </figure>
          <figure className="plot">
            <figcaption>
              <span dangerouslySetInnerHTML={{ __html: t(lang, 'kr.p2') }} />
              <span className="plot-legend">
                <span><i className="lg-solid" /><span dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lg1') }} /></span>
                <span><i className="lg-dash" /><span dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lg2') }} /></span>
              </span>
            </figcaption>
            <div className="plot-canvas-wrap">
              <canvas ref={kRef} height={220} role="img" aria-label={tx({ fr: 'Complexité de Krylov en fonction du temps', en: 'Krylov complexity over time' }, lang)}
                onMouseMove={onKMove} onMouseLeave={() => { setTipK(null); draw(); }} />
              {tipK && <div className="plot-tip" style={{ left: tipK.x, top: tipK.y }}>{tipK.text}</div>}
            </div>
          </figure>
        </div>
      </div>
      <p className="lab-foot" dangerouslySetInnerHTML={{ __html: t(lang, 'kr.lab.foot') }} />
    </div>
  );
}
