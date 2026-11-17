// Formules rendues par KaTeX au moment de la construction : aucun calcul
// ni dépendance côté navigateur, seulement le CSS et les polices de KaTeX.
import katex from 'katex';

export function tex(src: string, display = true): string {
  return katex.renderToString(src, { displayMode: display, throwOnError: false, strict: 'ignore' });
}

/** Rend une liste de formules ; utile pour transmettre du HTML pré-calculé à un îlot React. */
export function texMap(sources: string[]): Record<string, string> {
  return Object.fromEntries(sources.map((s) => [s, tex(s)]));
}
