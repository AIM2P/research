import { useState } from 'react';
import { t, tx, plain, type Bi, type Lang } from '../../i18n';

type Engine = 'llm' | 'sym' | 'formal';
interface System {
  id: string; x: number; y: number; label: string; star?: boolean;
  anchor?: 'start' | 'end' | 'middle'; dy?: number; tags: Engine[]; k: Bi; d: Bi;
}

const TAG: Record<Engine, { cls: string } & Bi> = {
  llm: { cls: 't-gold', fr: 'LLM', en: 'LLM' },
  sym: { cls: 't-coral', fr: 'Calcul symbolique', en: 'Symbolic computation' },
  formal: { cls: 't-teal', fr: 'Preuve formelle', en: 'Formal proof' },
};

// Positions vérifiées : chaque point est dans la bonne région du diagramme
// (cercles : LLM (260,170), symbolique (182,300), formel (338,300), rayon 140).
const SYSTEMS: System[] = [
  { id: 'aim', x: 260, y: 252, label: 'AIM²P', star: true, tags: ['llm', 'sym', 'formal'],
    k: { fr: 'Notre cible', en: 'Our target' },
    d: { fr: 'L’intersection des trois : raisonnement par LLM, calcul exact par SymPy et certification par Lean 4, réunis dans une même boucle d’auto-correction, et appliqués à la physique mathématique.',
         en: 'The intersection of all three: LLM reasoning, exact computation with SymPy and certification with Lean 4, joined in a single self-correction loop and applied to mathematical physics.' } },
  { id: 'r1', x: 222, y: 98, label: 'DeepSeek-R1', anchor: 'start', tags: ['llm'],
    k: { fr: 'LLM de raisonnement', en: 'Reasoning LLM' },
    d: { fr: 'Excellente intuition mathématique et brouillons de preuve rapides, mais aucune garantie formelle : une étape fausse peut passer inaperçue.',
         en: 'Strong mathematical intuition and fast proof drafts, but no formal guarantee: a wrong step can go unnoticed.' } },
  { id: 'o3', x: 292, y: 130, label: 'OpenAI o1 / o3', anchor: 'start', tags: ['llm'],
    k: { fr: 'LLM de raisonnement', en: 'Reasoning LLM' },
    d: { fr: 'Modèles de raisonnement généralistes. Très performants sur les problèmes de type olympiades, sans vérification formelle de leurs démonstrations.',
         en: 'General reasoning models. Very strong on olympiad-style problems, with no formal verification of their proofs.' } },
  { id: 'llemma', x: 174, y: 210, label: 'Llemma', anchor: 'end', tags: ['llm', 'sym'],
    k: { fr: 'LLM + outils symboliques', en: 'LLM + symbolic tools' },
    d: { fr: 'Modèle open source d’EleutherAI spécialisé en mathématiques. Excellent pour écrire du code Python/SymPy, mais il lui faut un vérificateur externe pour valider ses preuves.',
         en: 'EleutherAI’s open-source model specialised in mathematics. Excellent at writing Python/SymPy code, but it needs an external checker to validate its proofs.' } },
  { id: 'alphaproof', x: 325, y: 222, label: 'AlphaProof', anchor: 'start', tags: ['llm', 'formal'],
    k: { fr: 'LLM + Lean 4', en: 'LLM + Lean 4' },
    d: { fr: 'Google DeepMind. Apprentissage par renforcement et recherche arborescente avec Lean 4. Très performant aux olympiades, mais propriétaire, fermé et non appliqué à la physique théorique.',
         en: 'Google DeepMind. Reinforcement learning and tree search with Lean 4. Very strong at olympiads, but proprietary, closed and not applied to theoretical physics.' } },
  { id: 'dsp', x: 356, y: 199, label: 'DeepSeek-Prover-V1.5', anchor: 'start', tags: ['llm', 'formal'],
    k: { fr: 'LLM + Lean 4 · ICLR 2025', en: 'LLM + Lean 4 · ICLR 2025' },
    d: { fr: 'Utilise la vérification Lean 4 comme récompense et une variante de MCTS (RMaxTS) construite sur les messages du compilateur. La référence la plus proche de notre boucle, évaluée sur des mathématiques pures (miniF2F, ProofNet).',
         en: 'Uses Lean 4 verification as a reward and an MCTS variant (RMaxTS) built on compiler messages. The closest reference to our loop, evaluated on pure mathematics (miniF2F, ProofNet).' } },
  { id: 'copilot', x: 386, y: 176, label: 'Lean Copilot', anchor: 'start', tags: ['llm', 'formal'],
    k: { fr: 'LLM dans Lean 4', en: 'LLM inside Lean 4' },
    d: { fr: 'Exécute des LLM directement dans Lean 4 pour suggérer des tactiques et rechercher des preuves en temps réel.',
         en: 'Runs LLMs directly inside Lean 4 to suggest tactics and search for proofs in real time.' } },
  { id: 'sympy', x: 120, y: 322, label: 'SymPy', anchor: 'start', tags: ['sym'],
    k: { fr: 'Solveur symbolique', en: 'Symbolic solver' },
    d: { fr: 'Calcul algébrique exact, dérivation et simplification symboliques, en Python et en open source. Incapable, seul, de structurer une preuve logique.',
         en: 'Exact algebra, symbolic differentiation and simplification, open source and in Python. On its own, it cannot structure a logical proof.' } },
  { id: 'sage', x: 104, y: 366, label: 'SageMath', anchor: 'start', tags: ['sym'],
    k: { fr: 'Systèmes de calcul formel', en: 'Computer algebra systems' },
    d: { fr: 'SageMath, Wolfram Mathematica : des outils de calcul puissants, mais qui ne manipulent pas la logique formelle d’une démonstration.',
         en: 'SageMath, Wolfram Mathematica: powerful computation tools that do not handle the formal logic of a proof.' } },
  { id: 'lean', x: 440, y: 318, label: 'Lean 4 · Mathlib', anchor: 'middle', dy: -16, tags: ['formal'],
    k: { fr: 'Assistant de preuve', en: 'Proof assistant' },
    d: { fr: 'Rigueur absolue : chaque preuve est vérifiée par un noyau. En contrepartie, une courbe d’apprentissage abrupte et une écriture des tactiques très lente.',
         en: 'Absolute rigour: every proof is checked by a kernel. The price is a steep learning curve and very slow tactic writing.' } },
  { id: 'rocq', x: 420, y: 372, label: 'Rocq · Isabelle', anchor: 'middle', dy: -16, tags: ['formal'],
    k: { fr: 'Assistants de preuve', en: 'Proof assistants' },
    d: { fr: 'Rocq (ex-Coq) et Isabelle/HOL : la même exigence de rigueur, le même coût d’écriture manuelle.',
         en: 'Rocq (formerly Coq) and Isabelle/HOL: the same demand for rigour, the same cost of manual writing.' } },
  { id: 'physlean', x: 372, y: 414, label: 'PhysLean / Physlib', anchor: 'start', tags: ['formal'],
    k: { fr: 'Physique formalisée en Lean 4', en: 'Physics formalised in Lean 4' },
    d: { fr: 'Bibliothèque communautaire (ex-HepLean) : hautes énergies, théorème de Wick, information quantique. Elle montre que la physique formelle est possible, mais ne couvre pas, à notre connaissance, la complexité de Krylov.',
         en: 'Community library (formerly HepLean): high-energy physics, Wick’s theorem, quantum information. It shows formal physics is possible but, to our knowledge, does not cover Krylov complexity.' } },
];

function starPath(x: number, y: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const r = i % 2 ? 7 : 17, a = -Math.PI / 2 + (i * Math.PI) / 5;
    pts.push(`${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`);
  }
  return 'M' + pts.join('L') + 'Z';
}

export default function Venn({ lang }: { lang: Lang }) {
  const [activeId, setActiveId] = useState('aim');
  const active = SYSTEMS.find((s) => s.id === activeId) ?? SYSTEMS[0];
  // l'étoile est dessinée en dernier pour rester au-dessus
  const ordered = [...SYSTEMS.slice(1), SYSTEMS[0]];

  return (
    <div className="venn-wrap">
      <div className="venn-figure">
        <svg viewBox="0 0 520 480" className="venn" role="group" aria-label={lang === 'fr' ? 'Positionnement des systèmes existants' : 'Where existing systems stand'}>
          <defs>
            <radialGradient id="star-glow">
              <stop offset="0" stopColor="#F6B73C" stopOpacity=".55" />
              <stop offset="1" stopColor="#F6B73C" stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle className="vc vc-gold" cx="260" cy="170" r="140" />
          <circle className="vc vc-coral" cx="182" cy="300" r="140" />
          <circle className="vc vc-teal" cx="338" cy="300" r="140" />
          <text className="vl" x="260" y="20">{plain(t(lang, 'sota.v.llm'))}</text>
          <text className="vl" x="150" y="468">{plain(t(lang, 'sota.v.sym'))}</text>
          <text className="vl" x="380" y="468">{plain(t(lang, 'sota.v.formal'))}</text>
          {ordered.map((s) => {
            const anchor = s.star ? 'middle' : s.anchor ?? 'start';
            const dx = anchor === 'start' ? 12 : anchor === 'end' ? -12 : 0;
            const dy = s.star ? 34 : s.dy ?? 4.5;
            const select = () => setActiveId(s.id);
            return (
              <g
                key={s.id}
                className={'vdot' + (s.star ? ' vdot-star' : '') + (s.id === activeId ? ' is-active' : '')}
                tabIndex={0}
                role="button"
                aria-label={s.label}
                aria-pressed={s.id === activeId}
                onMouseEnter={select}
                onFocus={select}
                onClick={select}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(); } }}
              >
                {s.star ? (
                  <>
                    <circle cx={s.x} cy={s.y} r={46} fill="url(#star-glow)" />
                    <path className="star-shape" d={starPath(s.x, s.y)} />
                  </>
                ) : (
                  <circle cx={s.x} cy={s.y} r={6.5} />
                )}
                <text x={s.x + dx} y={s.y + dy} textAnchor={anchor}>{s.label}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <aside className="venn-info card" aria-live="polite">
        <p className="vi-k">{tx(active.k, lang)}</p>
        <h3>{active.label}</h3>
        <p>{tx(active.d, lang)}</p>
        <p className="vi-tags">
          {active.tags.map((tag) => <span key={tag} className={TAG[tag].cls}>{tx(TAG[tag], lang)}</span>)}
        </p>
      </aside>
    </div>
  );
}
