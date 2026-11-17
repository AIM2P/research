// Copie le logo, l'image de partage et les PDF depuis le dépôt de recherche,
// pour qu'il n'existe qu'une seule source de vérité (branding/ et docs/).
import { copyFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const web = join(dirname(fileURLToPath(import.meta.url)), '..');
const repo = join(web, '..');
const pub = join(web, 'public');

mkdirSync(join(pub, 'docs'), { recursive: true });
copyFileSync(join(repo, 'branding', 'aim2p-mark-transparent.svg'), join(pub, 'aim2p-mark.svg'));
copyFileSync(join(repo, 'branding', 'aim2p-banner.png'), join(pub, 'og.png'));
const pdfs = readdirSync(join(repo, 'docs', 'pdf')).filter((f) => f.endsWith('.pdf'));
for (const f of pdfs) copyFileSync(join(repo, 'docs', 'pdf', f), join(pub, 'docs', f));
console.log(`[sync-assets] logo, image de partage et ${pdfs.length} PDF copiés`);
