// The tiny inline scripts of the prerendered first screen. Plain strings, no import, so the build (vite.config.ts) and the
// checks (scripts/check_shell.mjs) can load this file anywhere.
//
// 1. The decision script (in the head, before the shell is parsed): which language and which market will this visitor read
//    (src/shared/lang.ts detectLang and src/shared/markets.ts detectMarket: ?lang=, ?m=, the visitor's earlier choice, the
//    market's language, the browser's)? It is the same rule in a few lines, written from the tables those modules hold (ShellRule,
//    filled in by the build from the modules themselves); scripts/check_shell.mjs runs both over a matrix of links, stored choices
//    and browsers and fails the build's check when they differ. The answer is left in window.__lpShell. Should the script itself
//    fail, the page is marked "lp-noshell" and the stylesheet hides the shell (src/landing/css/base.css): the visitor then waits
//    for React's first render.
// 2. The swap script (right after the shells): the shell in the body is English; German, Lithuanian and Hungarian ones sit next to
//    it as <template id="tpl-xx"> (src/landing/shell/render.tsx). When the visitor reads another language the swap puts that
//    template's markup in its place, before the first paint; it gives the links to /try the visitor's market (m=), and takes
//    away the language buttons of a language the visitor's market has no texts in (the Australian one: English and German).
// 3. The bar script (right after the swap): sets --bar-h, the height of the notice bar, before the first paint, because the
//    header and the hero are placed by it (on a narrow phone the bar is two lines, not one). The live page keeps it in step
//    afterwards (src/landing/shell/chrome.ts).
// 4. The loader (end of the body, build only): starts the page's own script after the LCP picture has loaded, see loaderScript.
// 5. The early ask (in the head): the two small API answers the page needs (see prefetchScript).

/** The tables of src/shared/markets.ts and src/shared/lang.ts the decision needs. */
export interface ShellRule {
  /** DEFAULT_MARKET. */
  defaultMarket: string;
  /** The markets a link or a stored choice may name (selectable). */
  selectable: string[];
  /** market -> the languages its legal edition has texts in (marketLangs). */
  allowed: Record<string, string[]>;
  /** market -> its own language when it names one that is not English (marketDefaultLang). */
  own: Record<string, string | null>;
}

export const MARKET_KEY = 'snapeyes.market';
export const LANG_KEY = 'snapeyes.lang';

export function decisionScript(rule: ShellRule): string {
  const data = JSON.stringify(rule);
  const hide = "document.documentElement.className+=' lp-noshell'";
  return (
    `(function(){try{var R=${data},q=new URLSearchParams(location.search),` +
    `st=function(k){try{return localStorage.getItem(k)}catch(e){return null}},` +
    `nm=function(v){return typeof v==='string'?v.trim().toLowerCase():null},` +
    `sel=function(v){return R.selectable.indexOf(v)>=0},` +
    `m=nm(q.get('m'));if(!sel(m)){m=st('${MARKET_KEY}');if(!sel(m))m=R.defaultMarket}` +
    `var al=R.allowed[m]||[],ok=function(v){return al.indexOf(v)>=0},l=q.get('lang');` +
    `if(!ok(l)){l=st('${LANG_KEY}');if(!ok(l)){l=R.own[m]||null;if(!l){var n=(navigator.language||'').toLowerCase();` +
    `n=n.indexOf('de')===0?'de':n.indexOf('lt')===0?'lt':n.indexOf('hu')===0?'hu':'en';l=ok(n)?n:'en'}}}` +
    `window.__lpShell={l:l,m:m}}catch(e){${hide}}})()`
  );
}

/** The swap (2): the visitor's language in place of the English shell, the visitor's market in the links to /try (the shells are made
 *  for the default market, whose links carry no m=; src/landing/config.ts tryUrl adds it for any other, and so does this) and, for a
 *  market whose edition has fewer languages than the site (fewer: market -> its languages), only its language buttons. */
export function swapScript(defaultMarket: string, fewer: Record<string, string[]>): string {
  return (
    `(function(){var s=window.__lpShell,sh=document.getElementById('shell'),F=${JSON.stringify(fewer)};if(!s||!sh)return;try{` +
    `if(s.l!=='en'){var t=document.getElementById('tpl-'+s.l);if(t)sh.innerHTML=t.innerHTML;document.documentElement.lang=s.l}` +
    `if(s.m!==${JSON.stringify(defaultMarket)}){var a=sh.querySelectorAll('a[href^="/try"]');` +
    `for(var i=0;i<a.length;i++)a[i].setAttribute('href',a[i].getAttribute('href')+'&m='+encodeURIComponent(s.m))}` +
    `if(F[s.m]){var b=sh.querySelectorAll('#langSeg button');for(var j=0;j<b.length;j++)if(F[s.m].indexOf(b[j].getAttribute('lang'))<0)b[j].remove()}}catch(e){}})()`
  );
}

/** The early ask (5): the page asks /api/health and /api/checkout once (src/landing/ordering.ts: is ordering open, and which market does
 *  the visitor's country suggest). Asked from the page's own script that happens about 2 s into a slow phone's load, after the first
 *  paint, and an answer that suggests another currency then adds the offer of it above the hero and pushes the page down (CLS 0.12 on
 *  a phone). Asked from here, at the first byte, the answers are in long before the page's script has loaded, ordering.ts takes them
 *  (window.__lpApi) and src/main.tsx lets React start with them known, so the offer is part of the first render that replaces the
 *  static first screen and nothing moves. A low priority: the LCP picture comes first. Nothing here decides anything. */
export const prefetchScript =
  "(function(){try{var o={headers:{Accept:'application/json'},cache:'no-store',credentials:'same-origin',priority:'low'},a={};" +
  "a['/api/health']=fetch('/api/health',o);a['/api/checkout']=fetch('/api/checkout',o);" +
  "a['/api/health'].catch(function(){});a['/api/checkout'].catch(function(){});window.__lpApi=a}catch(e){}})()";

export const barScript =
  "(function(){var b=document.getElementById('topbar'),r=document.documentElement;" +
  "function s(){r.style.setProperty('--bar-h',b.offsetHeight+'px')}s();addEventListener('resize',s);" +
  'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(s)})()';

/** The loader of the page's own script (4): the build takes the module script and its modulepreload links out of the head and this
 *  inline script adds them once the LCP picture has loaded (at once for a visitor the shell is not for, whose page has no such
 *  picture to wait for, and after 4 s whatever happens). Until then the phone's 1.6 Mbit/s carry the HTML, the two stylesheets, the
 *  two fonts and the picture, not 120 kB of script that only matters after the first paint: the picture arrives about 0.6 s earlier.
 *  The first screen needs no script (it is static, its links are links); React takes the page over a moment later. */
export function loaderScript(main: string, preloads: string[], langChunks: Record<string, string> = {}): string {
  return (
    `(function(){var M=${JSON.stringify(main)},P=${JSON.stringify(preloads)},C=${JSON.stringify(langChunks)},d=0;` +
    // the visitor's language file travels with the script instead of after it (the decision script left the language in window.__lpShell)
    `function go(){if(d)return;d=1;var w=window.__lpShell;if(w&&C[w.l])P=P.concat([C[w.l]]);` +
    `for(var i=0;i<P.length;i++){var l=document.createElement('link');l.rel='modulepreload';l.crossOrigin='';l.href=P[i];document.head.appendChild(l)}` +
    `var s=document.createElement('script');s.type='module';s.crossOrigin='';s.src=M;document.head.appendChild(s)}` +
    `var h=document.getElementById('heroImg');` +
    `if(!h||h.complete||document.documentElement.className.indexOf('lp-noshell')>=0)go();` +
    `else{h.addEventListener('load',go);h.addEventListener('error',go);setTimeout(go,4000)}})()`
  );
}
