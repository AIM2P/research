import { useRef, useState } from 'react';
import { t, tx, type Lang } from '../../i18n';

// Métadonnées reprises de CITATION.cff, à la racine du dépôt.
const CITES = {
  apa: 'AIM²P Initiative. (2026). AIM²P: Research Program for Certified AI Reasoning in Mathematics and Mathematical Physics (Phase 0) (Version 0.1.0). https://github.com/AIM2P/research',
  bibtex: [
    '@misc{aim2p_2026,',
    '  title   = {{AIM²P}: Research Program for Certified {AI} Reasoning in Mathematics and Mathematical Physics (Phase 0)},',
    '  author  = {{AIM²P Initiative}},',
    '  year    = {2026},',
    '  version = {0.1.0},',
    '  url     = {https://github.com/AIM2P/research},',
    '  note    = {License: CC BY 4.0}',
    '}',
  ].join('\n'),
} as const;
type Mode = keyof typeof CITES;

export default function CiteBox({ lang }: { lang: Lang }) {
  const [mode, setMode] = useState<Mode>('apa');
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  function flash() { setCopied(true); window.setTimeout(() => setCopied(false), 1800); }
  function selectText() {
    const el = codeRef.current;
    if (!el) return;
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel?.removeAllRanges();
    sel?.addRange(range);
  }
  function copy() {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(CITES[mode]).then(flash, selectText);
    } else selectText();
  }

  return (
    <div className="cite-box">
      <div className="cite-head">
        <h3 dangerouslySetInnerHTML={{ __html: t(lang, 'res.cite.t') }} />
        <div className="tabs" role="tablist">
          {(['apa', 'bibtex'] as Mode[]).map((m) => (
            <button key={m} type="button" role="tab" className="tab" aria-selected={mode === m} onClick={() => setMode(m)}>
              {m === 'apa' ? 'APA' : 'BibTeX'}
            </button>
          ))}
        </div>
        <button type="button" className="btn btn-ghost-dark btn-sm" onClick={copy}>
          <svg className="ico"><use href="#i-copy" /></svg>
          <span>{copied ? tx({ fr: 'Copié !', en: 'Copied!' }, lang) : tx({ fr: 'Copier', en: 'Copy' }, lang)}</span>
        </button>
      </div>
      <pre className="code cite-code"><code ref={codeRef}>{CITES[mode]}</code></pre>
    </div>
  );
}
