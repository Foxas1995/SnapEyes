// The two tiny inline scripts of the prerendered first screen. Plain strings, no import, so the build (vite.config.ts) and the
// checks (scripts/check_shell.mjs) can load this file anywhere.
//
// 1. The decision script (in the head, before the shell is parsed): the shell is the English first screen of the default
//    market. A visitor who will read another language or another market (src/shared/lang.ts detectLang and
//    src/shared/markets.ts detectMarket: ?lang=, ?m=, the visitor's earlier choice, the market's language, the browser's)
//    must never see it flash up in English, so the script marks the page "lp-noshell" and the stylesheet hides the shell
//    (src/landing/css/base.css). It is the same rule as detectLang and detectMarket in a few lines, written from the tables
//    those modules hold (ShellRule, filled in by the build from the modules themselves); scripts/check_shell.mjs runs both
//    over a matrix of links, stored choices and browsers and fails the build's check when they differ.
// 2. The bar script (right after the shell): sets --bar-h, the height of the notice bar, before the first paint, because the
//    header and the hero are placed by it (on a narrow phone the bar is two lines, not one). The live page keeps it in step
//    afterwards (src/landing/shell/chrome.ts).
// 3. The loader (end of the body, build only): starts the page's own script after the LCP picture has loaded, see loaderScript.

/** The tables of src/shared/markets.ts and src/shared/lang.ts the decision needs. */
export interface ShellRule {
  /** DEFAULT_MARKET and the language of the shell. */
  defaultMarket: string;
  lang: string;
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
    `if(l!==R.lang||m!==R.defaultMarket)${hide}}catch(e){${hide}}})()`
  );
}

export const barScript =
  "(function(){var b=document.getElementById('topbar'),r=document.documentElement;" +
  "function s(){r.style.setProperty('--bar-h',b.offsetHeight+'px')}s();addEventListener('resize',s);" +
  'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(s)})()';

/** The loader of the page's own script (3): the build takes the module script and its modulepreload links out of the head and this
 *  inline script adds them once the LCP picture has loaded (at once for a visitor the shell is not for, whose page has no such
 *  picture to wait for, and after 4 s whatever happens). Until then the phone's 1.6 Mbit/s carry the HTML, the two stylesheets, the
 *  two fonts and the picture, not 120 kB of script that only matters after the first paint: the picture arrives about 0.6 s earlier.
 *  The first screen needs no script (it is static, its links are links); React takes the page over a moment later. */
export function loaderScript(main: string, preloads: string[]): string {
  return (
    `(function(){var M=${JSON.stringify(main)},P=${JSON.stringify(preloads)},d=0;` +
    `function go(){if(d)return;d=1;for(var i=0;i<P.length;i++){var l=document.createElement('link');l.rel='modulepreload';l.crossOrigin='';l.href=P[i];document.head.appendChild(l)}` +
    `var s=document.createElement('script');s.type='module';s.crossOrigin='';s.src=M;document.head.appendChild(s)}` +
    `var h=document.getElementById('heroImg');` +
    `if(!h||h.complete||document.documentElement.className.indexOf('lp-noshell')>=0)go();` +
    `else{h.addEventListener('load',go);h.addEventListener('error',go);setTimeout(go,4000)}})()`
  );
}
