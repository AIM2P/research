import { strings, type StringKey } from './strings';

export type Lang = 'fr' | 'en';
export type Bi = { fr: string; en: string };
export type { StringKey };

/** Texte d'interface (peut contenir du HTML simple : à rendre avec set:html). */
export function t(lang: Lang, key: StringKey): string {
  return strings[lang][key] ?? strings.fr[key];
}

/** Version texte brut d'une chaîne (attributs aria-label, title…). */
export function plain(html: string): string {
  return html
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/** Typographie française : espace insécable avant : ; ! ? » % et après «, hors balises HTML. */
export function frSpace(s: string): string {
  return s
    .split(/(<[^>]+>)/)
    .map((part) =>
      part.startsWith('<')
        ? part
        : part.replace(/ ([:;!?»%])/g, ' $1').replace(/« /g, '« '),
    )
    .join('');
}

/** Choisit la langue d'un texte bilingue et applique la typographie française. */
export function tx(o: Bi, lang: Lang): string {
  return lang === 'fr' ? frSpace(o.fr) : o.en;
}

/* ---- Chemins ---------------------------------------------------------- */

const BASE = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');

/** Préfixe un chemin absolu du site avec le sous-chemin de publication éventuel. */
export function withBase(path: string): string {
  return BASE + (path.startsWith('/') ? path : '/' + path);
}

/** Construction de l'aperçu claude.ai : pages en fichiers .html, PDF lus sur GitHub. */
export const ARTIFACT = import.meta.env.PUBLIC_ARTIFACT === '1';

export function homeHref(lang: Lang): string {
  if (ARTIFACT) return withBase(lang === 'fr' ? '/' : '/en.html');
  return withBase(lang === 'fr' ? '/' : '/en/');
}

export function docHref(lang: Lang, slug: string): string {
  const dir = lang === 'fr' ? '/documents/' : '/en/documents/';
  return withBase(dir + slug + (ARTIFACT ? '.html' : '/'));
}

export const REPO_URL = 'https://github.com/AIM2P/research';

/** Lien vers le PDF d'un document : servi par le site, ou par GitHub dans l'aperçu. */
export function pdfHref(file: string): string {
  return ARTIFACT ? `${REPO_URL}/blob/main/docs/pdf/${file}.pdf` : withBase(`/docs/${file}.pdf`);
}

/** Attributs du lien PDF : téléchargement direct sur le site, nouvel onglet dans l'aperçu. */
export function pdfAttrs(): Record<string, string | boolean> {
  return ARTIFACT ? { target: '_blank', rel: 'noopener' } : { download: true };
}
export const ORG_URL = 'https://github.com/AIM2P';
