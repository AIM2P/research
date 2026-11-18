// Documents fondateurs : lus depuis ../docs/*.md (la source de vérité du dépôt)
// et transformés en HTML au moment de la construction du site.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { markdownToHtml } from 'satteri';
import { docHref, frSpace, type StringKey } from '../i18n';

export interface DocMeta {
  n: string;
  slug: string;
  file: string;
  titleKey: StringKey;
  descKey: StringKey;
}

export const DOCS: DocMeta[] = [
  { n: '00', slug: 'roadmap', file: '00_Roadmap_2026-2028', titleKey: 'res.d0.t', descKey: 'res.d0.d' },
  { n: '01', slug: 'research-question', file: '01_Research_Question', titleKey: 'res.d1.t', descKey: 'res.d1.d' },
  { n: '02', slug: 'state-of-the-art', file: '02_State_of_the_Art', titleKey: 'res.d2.t', descKey: 'res.d2.d' },
  { n: '03', slug: 'research-gap', file: '03_Research_Gap', titleKey: 'res.d3.t', descKey: 'res.d3.d' },
  { n: '04', slug: 'research-proposal', file: '04_Research_Proposal_v0.1', titleKey: 'res.d4.t', descKey: 'res.d4.d' },
  { n: '05', slug: 'domain-map', file: '05_Domain_Map', titleKey: 'res.d5.t', descKey: 'res.d5.d' },
];

export interface TocItem { id: string; text: string }
export interface RenderedDoc { html: string; toc: TocItem[]; subtitle: string; meta: string }

const DOCS_DIR = join(process.cwd(), '..', 'docs');

const CALLOUT_LABEL: Record<string, string> = {
  NOTE: 'Note', TIP: 'Conseil', IMPORTANT: 'Important', WARNING: 'Avertissement', CAUTION: 'Règle',
};

function slugify(text: string): string {
  return text
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/&[a-z]+;/g, ' ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function renderDoc(doc: DocMeta): RenderedDoc {
  const md = readFileSync(join(DOCS_DIR, doc.file + '.md'), 'utf8');
  let { html } = markdownToHtml(md, {});

  // 1. Le titre H1 est affiché par l'en-tête de page.
  html = html.replace(/<h1>[\s\S]*?<\/h1>\s*/, '');

  // 2. Les deux premières lignes (sous-titre en gras, ligne « Phase : … ») passent dans l'en-tête.
  let subtitle = '';
  let meta = '';
  html = html.replace(/^\s*<p><strong>([\s\S]*?)<\/strong><\/p>\s*/, (_, s: string) => { subtitle = s; return ''; });
  html = html.replace(/^\s*<p>((?:Statut|Phase)[\s\S]*?)<\/p>\s*(<hr\s*\/?>)?\s*/, (_, s: string) => { meta = s; return ''; });

  // 3. Encadrés GitHub (> [!NOTE], > [!IMPORTANT]…).
  html = html.replace(
    /<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*([\s\S]*?)<\/blockquote>/g,
    (_, type: string, rest: string) =>
      `<aside class="callout callout-${type.toLowerCase()}"><p class="callout-k">${CALLOUT_LABEL[type]}</p><p>${rest}</aside>`,
  );
  html = html.replace(/<p>\s*<\/p>/g, '');

  // 4. Identifiants de titres et table des matières.
  const toc: TocItem[] = [];
  const used = new Set<string>();
  html = html.replace(/<h([23])>([\s\S]*?)<\/h\1>/g, (_, level: string, inner: string) => {
    let id = slugify(inner) || 'section';
    while (used.has(id)) id += '-';
    used.add(id);
    if (level === '2') toc.push({ id, text: inner.replace(/<[^>]+>/g, '') });
    return `<h${level} id="${id}">${inner}</h${level}>`;
  });

  // 5. Tableaux défilants sur mobile, liens externes dans un nouvel onglet.
  html = html.replace(/<table>/g, '<div class="table-wrap"><table>').replace(/<\/table>/g, '</table></div>');
  html = html.replace(/<a href="(https?:[^"]+)">/g, '<a href="$1" target="_blank" rel="noopener">');
  // Liens entre documents (« 02_State_of_the_Art.md ») : vers la page du site (texte source en français).
  html = html.replace(/<a href="(?:\.\/)?(\d\d_[^"#]+)\.md(#[^"]*)?">/g, (m, file: string, hash?: string) => {
    const target = DOCS.find((d) => d.file === file);
    return target ? `<a href="${docHref('fr', target.slug)}${hash ?? ''}">` : m;
  });

  // 6. Typographie française (hors blocs de code) et périodes « 2026–2028 » insécables.
  const typo = (s: string) => frSpace(s).replace(/(\d{4})–(\d{4})/g, '<span class="nowrap">$1–$2</span>');
  html = html.split(/(<pre[\s\S]*?<\/pre>)/).map((part) => (part.startsWith('<pre') ? part : typo(part))).join('');

  return { html, toc, subtitle: typo(subtitle), meta: frSpace(meta) };
}
