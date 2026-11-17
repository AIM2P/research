// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';

// SITE_URL et BASE_PATH permettent de publier sous un sous-chemin
// (par exemple https://aim2p.github.io/research/ → BASE_PATH=/research).
// PUBLIC_ARTIFACT=1 produit l'aperçu claude.ai (voir scripts/build-artifact.mjs) :
// pages en fichiers .html, sortie dans .artifact/raw.
const ARTIFACT = process.env.PUBLIC_ARTIFACT === '1';

export default defineConfig({
  site: process.env.SITE_URL || undefined,
  base: ARTIFACT ? '/' : process.env.BASE_PATH || '/',
  outDir: ARTIFACT ? './.artifact/raw' : './dist',
  // L'aperçu réserve les noms commençant par « _ » : dossier « assets » au lieu de « _astro ».
  build: { format: ARTIFACT ? 'file' : 'directory', assets: ARTIFACT ? 'assets' : '_astro' },
  trailingSlash: 'ignore',
  integrations: [react()],
  devToolbar: { enabled: false },
});
