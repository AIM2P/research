import { useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react';
import { tx, type Lang } from '../../i18n';
import { CHAPTERS, PHASES, STATUS, type Phase } from '../../data/phases';

// Serpentin de 3 rangées × 6 étapes dans un repère 1000 × 480.
const XS = [90, 254, 418, 582, 746, 910];
const YS = [92, 252, 412];
const PATH = 'M30,92 L910,92 A80,80 0 0 1 910,252 L90,252 A80,80 0 0 0 90,412 L970,412';

const placed = PHASES.map((p, i) => {
  const row = Math.floor(i / 6), col = i % 6;
  return { ...p, x: row % 2 ? XS[5 - col] : XS[col], y: YS[row] };
});
const lastActive = PHASES.reduce((acc, p, i) => (p.status === 'done' || p.status === 'current' ? i : acc), -1);
const chapterStarts = placed.filter((p, i) => i === 0 || placed[i - 1].ch !== p.ch);

export default function RoadmapMap({ lang }: { lang: Lang }) {
  const [sel, setSel] = useState(Math.max(0, lastActive));
  const doneRef = useRef<SVGPathElement>(null);
  const [dash, setDash] = useState<string | undefined>('0 4000');
  const p: Phase = PHASES[sel];

  // Longueur du tracé parcouru, du départ jusqu'à la phase en cours.
  useLayoutEffect(() => {
    const path = doneRef.current;
    if (!path || lastActive < 0) return;
    const total = path.getTotalLength();
    const target = placed[lastActive];
    let best = 0, bestD = Infinity;
    for (let s = 0; s <= total; s += 4) {
      const pt = path.getPointAtLength(s);
      const d = Math.hypot(pt.x - target.x, pt.y - target.y);
      if (d < bestD) { bestD = d; best = s; }
    }
    setDash(`${best} ${total}`);
  }, []);

  const onKey = (i: number) => (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSel(i); }
  };

  return (
    <>
      <div className="map-wrap">
        <div className="map">
          <svg viewBox="0 0 1000 480" role="group" aria-label={tx({ fr: 'Feuille de route, 19 phases', en: 'Roadmap, 19 phases' }, lang)}>
            <path d={PATH} className="map-path" />
            <path d={PATH} className="map-path-done" ref={doneRef} style={{ strokeDasharray: dash }} />
            <text x={30} y={128} className="map-chapter" textAnchor="middle">2026</text>
            <text x={981} y={364} className="map-chapter" textAnchor="middle">2028</text>
            <circle cx={30} cy={92} r={6} fill="var(--gold)" />
            <path d="M970,412 l0,-34 l22,9 l-22,9" fill="var(--teal)" stroke="var(--ink)" strokeWidth={2} strokeLinejoin="round" />
            {chapterStarts.map((c) => (
              <text key={c.ch} x={c.x} y={c.y - 44} className="map-chapter" textAnchor="middle">{tx(CHAPTERS[c.ch], lang)}</text>
            ))}
            {placed.map((ph, i) => (
              <g
                key={ph.code}
                className={`map-node is-${ph.status}${i === sel ? ' is-selected' : ''}`}
                tabIndex={0}
                role="button"
                aria-pressed={i === sel}
                aria-label={`${ph.code} · ${tx(ph.t, lang)} · ${tx(STATUS[ph.status], lang)}`}
                transform={`translate(${ph.x} ${ph.y})`}
                onClick={() => setSel(i)}
                onMouseEnter={() => setSel(i)}
                onKeyDown={onKey(i)}
              >
                <circle r={30} className="halo" />
                <circle r={27} className="disc" />
                <text y={ph.code.length > 3 ? 5 : 6} className={ph.code.length > 3 ? 'code code-sm' : 'code'}>{ph.code}</text>
                <text y={54} className="lbl">{tx(ph.s, lang)}</text>
              </g>
            ))}
          </svg>
          <ol className="map-list">
            {PHASES.map((ph) => (
              <li key={ph.code} className={`is-${ph.status}`}>
                <b>{ph.code}</b>{tx(ph.t, lang)}
                <span className="ch">{tx(CHAPTERS[ph.ch], lang)} · {tx(STATUS[ph.status], lang)}</span>
                <p>{tx(ph.d, lang)}</p>
              </li>
            ))}
          </ol>
        </div>
        <aside className="map-detail card" aria-live="polite">
          <div className="md-top">
            <span className="md-code">{p.code}</span>
            <span className="md-status" data-s={p.status}>{tx(STATUS[p.status], lang)}</span>
          </div>
          <p className="md-chapter">{tx(CHAPTERS[p.ch], lang)}</p>
          <h3>{tx(p.t, lang)}</h3>
          <p>{tx(p.d, lang)}</p>
        </aside>
      </div>
    </>
  );
}
