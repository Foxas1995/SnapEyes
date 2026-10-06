// Vite's module runner without a config (`runnerImport(path, { configFile: false })`, how the build's own steps and the page-code tests load the page's TypeScript in Node) cannot
// transform a stylesheet: its CSS plugin wants the state a dev server or a build sets up and stops on the first `import './x.css'`. The page's lazy sections import their own
// stylesheet beside the component (src/landing/StyleGallery.tsx, Faq.tsx: "importing this file brings its own stylesheet"), and a render in Node has no use for it, so with this
// plugin a stylesheet is an empty module there. It changes nothing in a build or in the browser: only the Node-side loaders pass it (scripts/check_landing_assets.mjs
// renderLanding, scripts/run_ts_tests.mjs).
export function cssStub() {
  const id = '\0snapeyes-css-stub';
  return {
    name: 'snapeyes-css-stub',
    enforce: 'pre',
    resolveId(source) { return /\.css(\?.*)?$/.test(source) ? id : null; },
    load(name) { return name === id ? 'export default ""' : null; },
  };
}
