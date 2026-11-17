import { useEffect, useRef, useState } from 'react';
import { t, tx, type Lang } from '../../i18n';

// n² + n + 41 est premier pour n = 0…39, puis échoue à n = 40 (1681 = 41²).
const LAST = 41;
const FIRST_FAIL = 40;
const P = (n: number) => n * n + n + 41;

function smallestFactor(k: number): number {
  for (let d = 2; d * d <= k; d++) if (k % d === 0) return d;
  return k;
}
const isPrime = (k: number) => k > 1 && smallestFactor(k) === k;
const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

interface Props { lang: Lang; claimHtml: string }

export default function EulerTrap({ lang, claimHtml }: Props) {
  const [tested, setTested] = useState(-1); // dernier n testé
  const [running, setRunning] = useState(false);
  const timers = useRef<number[]>([]);

  useEffect(() => () => timers.current.forEach((id) => window.clearTimeout(id)), []);

  function stopTimers() {
    timers.current.forEach((id) => { window.clearTimeout(id); window.clearInterval(id); });
    timers.current = [];
  }

  function reset() { stopTimers(); setRunning(false); setTested(-1); }

  function run() {
    stopTimers();
    if (prefersReducedMotion()) { setTested(LAST); return; }
    setRunning(true);
    let n = -1;
    setTested(-1);
    const id = window.setInterval(() => {
      n += 1;
      setTested(n);
      if (!isPrime(P(n))) {
        window.clearInterval(id);
        // une pause, puis n = 41 pour enfoncer le clou
        timers.current.push(window.setTimeout(() => { setTested(LAST); setRunning(false); }, 1400));
      }
    }, 95);
    timers.current.push(id);
  }

  let message: string;
  if (tested < 0) {
    message = tx({ fr: 'Testons-la, un entier après l’autre.', en: 'Let’s test it, one integer at a time.' }, lang);
  } else if (tested < FIRST_FAIL) {
    const v = P(tested);
    message = tx({
      fr: `n = ${tested} : P(${tested}) = ${v}, premier <span class="good">✓</span> · ${tested + 1} cas sur ${tested + 1}.`,
      en: `n = ${tested}: P(${tested}) = ${v}, prime <span class="good">✓</span> · ${tested + 1} out of ${tested + 1} cases.`,
    }, lang);
  } else {
    const v = P(FIRST_FAIL), f = smallestFactor(v);
    message = tx({
      fr: `<span class="bad">n = 40 : P(40) = ${v} = ${f} × ${v / f}.</span> Après 40 succès d’affilée, la conjecture est <strong>fausse</strong>.`,
      en: `<span class="bad">n = 40: P(40) = ${v} = ${f} × ${v / f}.</span> After 40 successes in a row, the conjecture is <strong>false</strong>.`,
    }, lang);
  }

  return (
    <article className="card euler">
      <header className="card-head">
        <span className="pill pill-coral" dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.pill') }} />
        <h3 dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.title') }} />
      </header>
      <p className="euler-claim">
        <span dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.claim') }} />
        <span className="math-block" dangerouslySetInnerHTML={{ __html: claimHtml }} />
      </p>
      <div className="euler-grid" role="list" aria-label={lang === 'fr' ? 'Valeurs de n testées' : 'Values of n tested'}>
        {Array.from({ length: LAST + 1 }, (_, n) => {
          const state = n > tested ? '' : isPrime(P(n)) ? ' is-prime' : ' is-comp';
          return (
            <span key={n} role="listitem" className={'cell' + state} title={n <= tested ? `P(${n}) = ${P(n)}` : undefined}>
              {n}
            </span>
          );
        })}
      </div>
      <div className="euler-readout" aria-live="polite">
        <p dangerouslySetInnerHTML={{ __html: message }} />
      </div>
      <div className="euler-actions">
        <button type="button" className="btn btn-primary" onClick={run} disabled={running}>
          <svg className="ico"><use href="#i-play" /></svg>
          <span dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.run') }} />
        </button>
        <button type="button" className="btn btn-ghost-dark" onClick={reset} dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.reset') }} />
      </div>
      <p className="euler-moral" dangerouslySetInnerHTML={{ __html: t(lang, 'man.e.moral') }} />
    </article>
  );
}
