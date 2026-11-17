// Construit l'aperçu claude.ai du site (artefact multipage).
//  1. astro build avec PUBLIC_ARTIFACT=1 → .artifact/raw (pages en .html)
//  2. chemins absolus → chemins relatifs (l'aperçu est servi sous un sous-chemin)
//  3. page d'accueil FR → .artifact/page.html, sans <html>/<head>/<body>
//     (l'hébergeur l'enveloppe lui-même) ; les autres fichiers sont listés
//     dans .artifact/files.json pour la publication.
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, readdirSync, statSync, rmSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const web = join(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(web, '.artifact');
const raw = join(out, 'raw');

rmSync(out, { recursive: true, force: true });
execSync('node scripts/sync-assets.mjs && npx astro build', {
  cwd: web, stdio: 'inherit', env: { ...process.env, PUBLIC_ARTIFACT: '1' },
});

const walk = (dir) => readdirSync(dir).flatMap((f) => {
  const p = join(dir, f);
  return statSync(p).isDirectory() ? walk(p) : [p];
});
const rel = (p) => relative(raw, p).split('\\').join('/');

// Toutes les sections visibles dès le chargement (vignettes, liens partagés).
const AT_REST = '<style>.js .reveal{opacity:1!important;transform:none!important;transition:none!important}</style>';
// Les navigateurs actuels ne chargent que le .woff2 : .woff et .ttf (polices de repli) ne sont pas publiés.
const EXCLUDE = (path) => path === '404.html' || path === 'og.png' || path.startsWith('docs/') || /\.(woff|ttf)$/.test(path);

const published = [];
for (const file of walk(raw)) {
  const path = rel(file);
  if (EXCLUDE(path)) continue;

  if (path.endsWith('.html')) {
    const depth = path.split('/').length - 1;
    const prefix = depth ? '../'.repeat(depth) : './';
    let html = readFileSync(file, 'utf8')
      .replace(/(\s(?:href|src|component-url|renderer-url|before-hydration-url)=")\/(?!\/)/g, `$1${prefix}`)
      .replace(/url\(\/(?!\/)/g, `url(${prefix}`);

    if (path === 'index.html') {
      const head = html.slice(html.indexOf('<head>') + 6, html.indexOf('</head>'))
        .replace(/<meta charset="[^"]*"\s*\/?>/, '')
        .replace(/<meta name="viewport"[^>]*>/, '')
        .replace(/<title>[\s\S]*?<\/title>/, '');
      const body = html.slice(html.indexOf('<body>') + 6, html.lastIndexOf('</body>'));
      const page = [
        '<title>AIM²P</title>',
        '<meta name="claude:viewport-fit-sides" content="cover">',
        '<script>document.documentElement.lang = "fr";</script>',
        head.trim(),
        AT_REST,
        body.trim(),
      ].join('\n');
      writeFileSync(join(out, 'page.html'), page);
      continue;
    }
    writeFileSync(file, html.replace('</head>', AT_REST + '</head>'));
  } else if (path.endsWith('.css')) {
    writeFileSync(file, readFileSync(file, 'utf8').replace(/url\(\/assets\//g, 'url(./'));
  } else if (path.endsWith('.js')) {
    const js = readFileSync(file, 'utf8');
    if (js.includes('"/assets/')) console.warn(`[artifact] chemin absolu restant dans ${path}`);
  }
  published.push(path);
}

writeFileSync(join(out, 'files.json'), JSON.stringify(published.map((path) => ({ path })), null, 0));
const size = published.reduce((s, p) => s + statSync(join(raw, p)).size, 0);
console.log(`[artifact] page.html + ${published.length} fichiers (${(size / 1048576).toFixed(1)} Mo)`);
