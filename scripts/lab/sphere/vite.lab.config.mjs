// LAB: a production build of the centrepiece prototypes alone (src/lab/sphere.html), to measure what the landing would carry: the size of the lazy
// chunk of each prototype (gzip) and the frame rate of minified code (./fps.mjs). The site's own build (vite.config.ts) never sees this page.
//
//   npx vite build --config scripts/lab/sphere/vite.lab.config.mjs          (SX_OUT=<dir> to choose the output, default ../sphere_dist next to the repo)
//   npx vite preview --config scripts/lab/sphere/vite.lab.config.mjs --port 5282 --host 127.0.0.1
//   then http://127.0.0.1:5282/src/lab/sphere.html?p=globe
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../..');

export default defineConfig({
  root,
  plugins: [react(), tailwindcss()],
  build: {
    outDir: process.env.SX_OUT || resolve(root, '../sphere_dist'),
    emptyOutDir: true,
    // every picture stays a file of its own (a small thumbnail must not end up inside the chunk as base64)
    assetsInlineLimit: 0,
    rollupOptions: { input: { sphere: resolve(root, 'src/lab/sphere.html') } },
  },
});
