// The capture tool's language, by the site's one rule (src/shared/lang.ts detectLang): ?lang= wins, then the visitor's
// earlier choice (localStorage "snapeyes.lang", shared by every page), then the market's own language (lt, hu), then the
// browser language. Re-exported here so /try and /order do not import the landing page's whole copy, which would then
// ride in the chunk both pages load.
export { detectLang, isLang, rememberLang, type Lang } from '../shared/lang';
