import { useEffect, useState, type KeyboardEvent } from 'react';
import { t, tx, plain, type Bi, type Lang } from '../../i18n';

/* La boucle LLM → Lean 4 → SymPy → correction → Lean 4, rejouée pas à pas
   sur un lemme réel : la somme des n premiers impairs vaut n². */

type Node = 'llm' | 'sympy' | 'lean' | 'fix' | null;
type State = 'idle' | 'work' | 'error' | 'ok';
interface Block { lang: 'lean' | 'py' | 'lean-out'; src: string | Bi; cls?: string }
interface Step { node: Node; state: State; iter: number; k: Bi; t: Bi; d: Bi; tex?: string; code?: Block; out?: Block; badge: Bi }

const STATEMENT = 'theorem sum_odd (n : ℕ) :\n    ∑ k ∈ Finset.range n, (2 * k + 1) = n ^ 2 := by\n';
const V1 = STATEMENT + '  induction n with\n  | zero => simp\n  | succ n ih =>\n    rw [Finset.sum_range_succ, ih]';
const V2 = V1 + '\n+   ring';

export const WORKSHOP_TEX = ['\\sum_{k=0}^{n-1} (2k+1) = n^2', 'n^2 + (2n+1) - (n+1)^2 = 0'];

const STEPS: Step[] = [
  {
    node: null, state: 'idle', iter: 1,
    k: { fr: 'Énoncé', en: 'Statement' },
    t: { fr: 'Montrer que la somme des n premiers impairs vaut n².', en: 'Show that the sum of the first n odd numbers is n².' },
    d: { fr: 'Un lemme simple, choisi pour que chaque étape de la boucle reste lisible. Le mot-clé <code>sorry</code> marque la preuve qui manque.',
         en: 'A simple lemma, chosen so that every step of the loop stays readable. The keyword <code>sorry</code> marks the missing proof.' },
    tex: WORKSHOP_TEX[0],
    code: { lang: 'lean', src: STATEMENT + '  sorry' },
    badge: { fr: 'à prouver', en: 'to prove' },
  },
  {
    node: 'llm', state: 'work', iter: 1,
    k: { fr: '1 · Raisonner · LLM', en: '1 · Reason · LLM' },
    t: { fr: 'Le LLM propose une stratégie : la récurrence.', en: 'The LLM proposes a strategy: induction.' },
    d: { fr: 'Cas de base : la somme vide vaut 0 = 0². Hérédité : on isole le dernier terme avec <code>Finset.sum_range_succ</code>, puis on applique l’hypothèse de récurrence <code>ih</code>.',
         en: 'Base case: the empty sum is 0 = 0². Inductive step: split off the last term with <code>Finset.sum_range_succ</code>, then apply the induction hypothesis <code>ih</code>.' },
    code: { lang: 'lean', src: V1 },
    badge: { fr: 'brouillon v1', en: 'draft v1' },
  },
  {
    node: 'lean', state: 'error', iter: 1,
    k: { fr: '2 · Certifier · Lean 4', en: '2 · Certify · Lean 4' },
    t: { fr: 'Lean refuse : un but reste ouvert.', en: 'Lean refuses: one goal is still open.' },
    d: { fr: 'Le cas de base passe. Mais après les réécritures, il reste une égalité à établir. Lean ne devine rien : il indique exactement ce qui manque.',
         en: 'The base case goes through. But after the rewrites, an equality remains to be proved. Lean guesses nothing: it states exactly what is missing.' },
    out: { lang: 'lean-out', cls: 'is-error', src: 'error: unsolved goals\ncase succ\nn : ℕ\nih : ∑ k ∈ Finset.range n, (2 * k + 1) = n ^ 2\n⊢ n ^ 2 + (2 * n + 1) = (n + 1) ^ 2' },
    badge: { fr: '1 erreur', en: '1 error' },
  },
  {
    node: 'sympy', state: 'work', iter: 1,
    k: { fr: '3 · Calculer · SymPy', en: '3 · Compute · SymPy' },
    t: { fr: 'SymPy examine le but restant.', en: 'SymPy examines the remaining goal.' },
    d: { fr: 'La différence entre les deux membres se simplifie exactement en 0 : le but est une identité polynomiale, vraie pour tout n. La tactique adaptée est donc <code>ring</code>.',
         en: 'The difference between both sides simplifies exactly to 0: the goal is a polynomial identity, true for every n. The right tactic is therefore <code>ring</code>.' },
    tex: WORKSHOP_TEX[1],
    code: { lang: 'py', src: ">>> from sympy import symbols, expand\n>>> n = symbols('n', integer=True, nonnegative=True)\n>>> expand(n**2 + (2*n + 1) - (n + 1)**2)\n0" },
    badge: { fr: 'diagnostic', en: 'diagnosis' },
  },
  {
    node: 'fix', state: 'work', iter: 2,
    k: { fr: '4 · Corriger · retour du compilateur', en: '4 · Correct · compiler feedback' },
    t: { fr: 'Le correctif est réinjecté dans la preuve.', en: 'The fix is fed back into the proof.' },
    d: { fr: 'Le message de Lean et le diagnostic de SymPy repartent vers le raisonnement. Le correctif est minimal et ciblé : une seule ligne.',
         en: 'Lean’s message and SymPy’s diagnosis go back to the reasoning engine. The fix is minimal and targeted: a single line.' },
    code: { lang: 'lean', src: V2 },
    badge: { fr: 'brouillon v2', en: 'draft v2' },
  },
  {
    node: 'lean', state: 'ok', iter: 2,
    k: { fr: '5 · Certifier · Lean 4', en: '5 · Certify · Lean 4' },
    t: { fr: 'Certifié.', en: 'Certified.' },
    d: { fr: 'Le noyau de Lean accepte la preuve. Elle vaut pour <strong>tout</strong> entier n, pas seulement pour les exemples testés. C’est toute la différence entre « convaincant » et « vrai ».',
         en: 'Lean’s kernel accepts the proof. It holds for <strong>every</strong> integer n, not only for the examples tested. That is the whole difference between “convincing” and “true”.' },
    out: { lang: 'lean-out', cls: 'is-ok', src: {
      fr: '✓ Lean 4 : 0 erreur, 0 but restant\n✓ theorem sum_odd vérifié par le noyau\n  itérations de la boucle : 2',
      en: '✓ Lean 4: 0 errors, 0 goals remaining\n✓ theorem sum_odd checked by the kernel\n  loop iterations: 2' } },
    badge: { fr: 'certifié', en: 'certified' },
  },
];

/* --- Coloration syntaxique minimale ---------------------------------- */
const esc = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]!);
const line = (cls: string, html: string) => `<span class="ln${cls ? ' ' + cls : ''}">${html || ' '}</span>`;

function hlLean(src: string) {
  return src.split('\n').map((raw) => {
    let cls = '';
    if (raw.startsWith('+')) { cls = 'ln-add'; raw = ' ' + raw.slice(1); }
    const h = esc(raw)
      .replace(/\b(theorem|lemma|by|with|induction|fun|def)\b/g, '<span class="tk-kw">$1</span>')
      .replace(/\b(simp|rw|ring|sorry|exact|omega)\b/g, '<span class="tk-tac">$1</span>')
      .replace(/(^|[^\w])(\d+)(?![\w])/g, '$1<span class="tk-num">$2</span>');
    return line(cls, h);
  }).join('');
}
function hlPy(src: string) {
  return src.split('\n').map((raw) => {
    if (!raw.startsWith('>>> ')) return line('', `<span class="tk-ok">${esc(raw)}</span>`);
    const body = esc(raw.slice(4))
      .replace(/('[^']*')/g, '<span class="tk-str">$1</span>')
      .replace(/\b(from|import|True|False)\b/g, '<span class="tk-kw">$1</span>')
      .replace(/(^|[^\w'])(\d+)(?![\w])/g, '$1<span class="tk-num">$2</span>');
    return line('', '<span class="tk-com">&gt;&gt;&gt; </span>' + body);
  }).join('');
}
function hlOut(src: string) {
  return src.split('\n').map((raw) => {
    let h = esc(raw);
    if (raw.startsWith('error:')) h = '<span class="tk-err">error:</span>' + h.slice(6);
    else if (raw.startsWith('⊢')) h = `<span class="tk-goal">${h}</span>`;
    else if (raw.startsWith('✓')) h = `<span class="tk-ok">${h}</span>`;
    else if (raw.startsWith('case ')) h = `<span class="tk-com">${h}</span>`;
    return line('', h);
  }).join('');
}
function highlight(b: Block, lang: Lang) {
  const src = typeof b.src === 'string' ? b.src : b.src[lang];
  return b.lang === 'py' ? hlPy(src) : b.lang === 'lean-out' ? hlOut(src) : hlLean(src);
}

const NODES: { id: Exclude<Node, null>; x: number; y: number; label: Bi }[] = [
  { id: 'llm', x: 160, y: 48, label: { fr: 'LLM', en: 'LLM' } },
  { id: 'sympy', x: 272, y: 160, label: { fr: 'SymPy', en: 'SymPy' } },
  { id: 'lean', x: 160, y: 272, label: { fr: 'Lean 4', en: 'Lean 4' } },
  { id: 'fix', x: 48, y: 160, label: { fr: 'Corriger', en: 'Fix' } },
];

interface Props { lang: Lang; math: Record<string, string> }

export default function ProofWorkshop({ lang, math }: Props) {
  const [idx, setIdx] = useState(0);
  const [seen, setSeen] = useState(0);
  const [auto, setAuto] = useState(false);
  const step = STEPS[idx];
  const last = STEPS.length - 1;

  function go(i: number) {
    const n = (i + STEPS.length) % STEPS.length;
    setIdx(n);
    setSeen((s) => (n === 0 ? 0 : Math.max(s, n)));
  }

  // Lecture automatique : une étape toutes les 3,6 s, arrêt à la dernière.
  useEffect(() => {
    if (!auto) return;
    if (idx >= last) { setAuto(false); return; }
    const id = window.setTimeout(() => go(idx + 1), 3600);
    return () => window.clearTimeout(id);
  }, [auto, idx]);

  function toggleAuto() {
    if (auto) { setAuto(false); return; }
    if (idx === last) go(0);
    setAuto(true);
  }
  function onKey(e: KeyboardEvent) {
    if (e.key === 'ArrowRight' && idx < last) { setAuto(false); go(idx + 1); }
    if (e.key === 'ArrowLeft' && idx > 0) { setAuto(false); go(idx - 1); }
  }

  const center = step.state === 'ok' ? tx({ fr: '✓ certifié', en: '✓ certified' }, lang)
    : step.state === 'error' ? tx({ fr: '✗ refusé', en: '✗ rejected' }, lang) : 'theorem';

  return (
    <div className="workshop" data-state={step.state} onKeyDown={onKey}>
      <div className="ws-top">
        <div className="ws-title">
          <span className="ws-dots" aria-hidden="true"><i /><i /><i /></span>
          <h3 dangerouslySetInnerHTML={{ __html: t(lang, 'ws.title') }} />
          <span className="pill pill-outline" dangerouslySetInnerHTML={{ __html: t(lang, 'ws.badge') }} />
        </div>
        <div className="ws-meta">
          <span className="ws-iter">{tx({ fr: 'Itération ', en: 'Iteration ' }, lang)}{step.iter}</span>
          <span className="ws-state" data-state={step.state}>{tx(step.badge, lang)}</span>
        </div>
      </div>

      <div className="ws-body">
        <div className="ws-loop">
          <svg viewBox="0 0 320 320" className="loop-svg" role="img" aria-label={tx({ fr: 'Raisonner, calculer, certifier, corriger', en: 'Reason, compute, certify, correct' }, lang)}>
            <circle className="loop-track" cx="160" cy="160" r="112" />
            <circle className="loop-runner" cx="160" cy="160" r="112" />
            {NODES.map((n) => {
              const on = n.id === step.node;
              const cls = 'loop-node' + (on ? ' is-active' : '') + (on && step.state === 'error' ? ' is-error' : '');
              return (
                <g key={n.id} className={cls} data-node={n.id} transform={`translate(${n.x} ${n.y})`}>
                  <circle r="30" />
                  <text y="5">{tx(n.label, lang)}</text>
                </g>
              );
            })}
            <text className="loop-center-k" x="160" y="150">{center}</text>
            <text className="loop-center-v" x="160" y="178">sum_odd</text>
          </svg>
        </div>

        <div className="ws-console is-swapping" aria-live="polite" key={idx + lang}>
          <p className="ws-step-k" data-engine={step.node ?? 'problem'}>{tx(step.k, lang)}</p>
          <h4 className="ws-step-t">{tx(step.t, lang)}</h4>
          <p className="ws-step-d" dangerouslySetInnerHTML={{ __html: tx(step.d, lang) }} />
          {step.tex && <div className="ws-math" dangerouslySetInnerHTML={{ __html: math[step.tex] ?? step.tex }} />}
          {step.code && <pre className="code"><code dangerouslySetInnerHTML={{ __html: highlight(step.code, lang) }} /></pre>}
          {step.out && <pre className={'code code-out ' + (step.out.cls ?? '')}><code dangerouslySetInnerHTML={{ __html: highlight(step.out, lang) }} /></pre>}
        </div>
      </div>

      <div className="ws-foot">
        <div className="ws-progress" role="tablist" aria-label={tx({ fr: 'Étapes', en: 'Steps' }, lang)}>
          {STEPS.map((s, i) => (
            <button
              key={i}
              type="button"
              role="tab"
              aria-selected={i === idx}
              className={i <= seen && i !== idx ? 'is-seen' : undefined}
              aria-label={`${tx({ fr: 'Étape ', en: 'Step ' }, lang)}${i + 1} · ${tx(s.k, lang)}`}
              onClick={() => { setAuto(false); go(i); }}
            />
          ))}
        </div>
        <div className="ws-controls">
          <button type="button" className="btn btn-ghost-dark btn-sm" disabled={idx === 0} aria-label={plain(t(lang, 'ws.prev'))} onClick={() => { setAuto(false); go(idx - 1); }}>
            <svg className="ico"><use href="#i-prev" /></svg>
          </button>
          <button type="button" className="btn btn-primary btn-sm" id="ws-next" onClick={() => { setAuto(false); go(idx === last ? 0 : idx + 1); }}>
            <span>{idx === last ? tx({ fr: 'Rejouer', en: 'Replay' }, lang) : tx({ fr: 'Étape suivante', en: 'Next step' }, lang)}</span>
            <svg className="ico"><use href="#i-next" /></svg>
          </button>
          <button type="button" className="btn btn-ghost-dark btn-sm" id="ws-auto" aria-pressed={auto} onClick={toggleAuto}>
            <svg className="ico"><use href={auto ? '#i-pause' : '#i-play'} /></svg>
            <span dangerouslySetInnerHTML={{ __html: t(lang, 'ws.auto') }} />
          </button>
        </div>
      </div>
    </div>
  );
}
