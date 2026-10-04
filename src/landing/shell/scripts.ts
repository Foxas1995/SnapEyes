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
// 6. The menu (right after the bar script): the dialog of the narrow widths opens and closes, see menuScript.

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
 *  market whose edition has fewer languages than the site (fewer: market -> its languages), only its language buttons.
 *
 *  It also answers a click on a language button of the shell. Until React has taken the page over (about 2 s on a slow phone) the
 *  buttons would be dead and the tap lost; now the shell puts the chosen language's first screen in place, remembers the choice the way
 *  the live page does (localStorage "snapeyes.lang" and ?lang= in the address, src/shared/lang.ts rememberLang), and gives the new
 *  button the focus (the markup was replaced). React then starts in that language: detectLang reads exactly those two. */
export function swapScript(defaultMarket: string, fewer: Record<string, string[]>, langKey: string = LANG_KEY): string {
  return (
    `(function(){var s=window.__lpShell,sh=document.getElementById('shell'),F=${JSON.stringify(fewer)};if(!s||!sh)return;` +
    // the English markup is the shell's own; put(l) makes the shell read l from it or from l's template, fix() applies the market
    `var en=sh.innerHTML;function fix(){try{` +
    `if(s.m!==${JSON.stringify(defaultMarket)}){var a=sh.querySelectorAll('a[href^="/try"]');` +
    `for(var i=0;i<a.length;i++)a[i].setAttribute('href',a[i].getAttribute('href')+'&m='+encodeURIComponent(s.m))}` +
    `if(F[s.m]){var b=sh.querySelectorAll('#langSeg button');for(var j=0;j<b.length;j++)if(F[s.m].indexOf(b[j].getAttribute('lang'))<0)b[j].remove()}}catch(e){}}` +
    `function put(l){try{if(l==='en')sh.innerHTML=en;else{var t=document.getElementById('tpl-'+l);if(t)sh.innerHTML=t.innerHTML}` +
    `document.documentElement.lang=l;s.l=l}catch(e){}fix()}` +
    `if(s.l!=='en')put(s.l);else fix();` +
    `sh.addEventListener('click',function(e){try{var c=e.target&&e.target.closest&&e.target.closest('#langSeg button[lang]');if(!c)return;` +
    `var l=c.getAttribute('lang');if(!l||l===s.l)return;put(l);` +
    `try{localStorage.setItem('${langKey}',l)}catch(x){}` +
    `try{var u=new URL(location.href);u.searchParams.set('lang',l);history.replaceState(null,'',u)}catch(x){}` +
    `var n=sh.querySelector('#langSeg button[lang="'+l+'"]');if(n)n.focus()}catch(x){}})})()`
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

/** The menu (6): the header's menu button (below 960 px) opens the page's links in a native dialog (src/landing/MenuDialog.tsx), a chosen link
 *  closes it, and a window that grows to 960 px closes it (the header shows the navigation itself from there). The close button of the dialog is a
 *  form method="dialog" and Escape is the browser's: neither needs a script. One handler on the document, looking elements up by id at the
 *  moment of the click, so the same few lines serve the static first screen, the live page after React took over, and every language. */
export const menuScript =
  "(function(){var D=document;function m(){return D.getElementById('menu')}" +
  "D.addEventListener('click',function(e){try{var t=e.target,d=m();if(!d||!t||!t.closest)return;" +
  "var b=t.closest('#menuBtn');if(b){if(d.showModal&&!d.open){d.showModal();b.setAttribute('aria-expanded','true')}return}" +
  "if(d.open&&t.closest('#menu a'))d.close()}catch(x){}});" +
  "D.addEventListener('close',function(e){var b=D.getElementById('menuBtn');if(e.target&&e.target.id==='menu'&&b)b.setAttribute('aria-expanded','false')},true);" +
  "try{window.matchMedia('(min-width:960px)').addEventListener('change',function(e){var d=m();if(e.matches&&d&&d.open)d.close()})}catch(x){}})()";

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
