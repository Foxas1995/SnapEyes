// LAB: the page of the two centrepiece prototypes (see ./main.tsx, which starts it).
import { useEffect, useState, type ComponentType } from 'react';
import { BrandPicture } from '../shared/BrandLogo';
import { WORDS, type Lang } from './sphere/words';
import type { PieceProps } from './sphere/Globe';

const q = new URLSearchParams(location.search);
const piece: 'globe' | 'ring' = q.get('p') === 'ring' ? 'ring' : 'globe';
const lang: Lang = (['en', 'de', 'lt', 'hu'] as const).find((l) => l === q.get('lang')) ?? 'lt';
const ui = q.get('ui') !== '0' && !q.has('rec');
const shot = q.has('shot');
const rec = q.has('rec');

const posters = import.meta.glob<string>('./poster/*.webp', { eager: true, query: '?url', import: 'default' });
const poster = (w: number) => posters[`./poster/${piece}-${w}.webp`];

interface Hero {
  title: string;
  cta: string;
}

// each prototype is fetched from a place of its own: with both import() calls in one function (an if or a conditional) the bundler gave
// the two chunks a single preload list, the globe's, and the ring arrived without its stylesheet
const loaders: Record<'globe' | 'ring', () => Promise<{ default: ComponentType<PieceProps> }>> = {
  globe: () => import('./sphere/Globe'),
  ring: () => import('./sphere/Ring'),
};
const load = (): Promise<ComponentType<PieceProps>> => loaders[piece]().then((m) => m.default);

function Stage() {
  const [Piece, setPiece] = useState<ComponentType<PieceProps> | null>(null);
  const [ready, setReady] = useState(false);
  const small = poster(640);
  const large = poster(1200);
  useEffect(() => {
    let alive = true;
    const go = () => load().then((c) => alive && setPiece(() => c));
    if (shot || rec || !small) go();
    else {
      // the poster first; the chunk when the browser has a moment
      const img = document.querySelector<HTMLImageElement>('.lab-poster');
      const idle = () => ('requestIdleCallback' in window ? requestIdleCallback(() => go(), { timeout: 1500 }) : setTimeout(go, 200));
      if (img && !img.complete) img.addEventListener('load', idle, { once: true });
      else idle();
    }
    return () => {
      alive = false;
    };
  }, [small]);
  const tryHref = `/try?lang=${lang}`;
  return (
    <div className={`lab-frame lab-${piece}`} data-ready={ready ? '' : undefined}>
      {small && !shot && (
        <img
          className="lab-poster"
          src={small}
          srcSet={`${small} 640w, ${large} 1200w`}
          sizes="(min-width: 960px) 600px, 100vw"
          alt=""
          fetchPriority="high"
          style={ready && rec ? { opacity: 0 } : undefined}
        />
      )}
      {Piece && <Piece words={WORDS[lang]} tryHref={tryHref} onReady={() => setReady(true)} />}
    </div>
  );
}

export default function Lab() {
  const [hero, setHero] = useState<Hero | null>(null);
  useEffect(() => {
    import(`../landing/copy/${lang}.json`).then((m: { default: { cta: string; hero: { title: string } } }) => setHero({ title: m.default.hero.title, cta: m.default.cta }));
  }, []);
  if (shot) return <Stage />;
  const go = (p: string) => {
    const u = new URL(location.href);
    u.searchParams.set('p', p);
    location.href = u.toString();
  };
  return (
    <>
      <header className="lab-hdr">
        <div className="lp-wrap">
          <a className="lp-logo" href="#top" aria-label="SnapEyes">
            <BrandPicture />
            <span>
              <b>SNAPEYES</b>
            </span>
          </a>
          {ui && (
            <div className="lab-switch" role="group" aria-label="Lab">
              <button type="button" aria-pressed={piece === 'globe'} onClick={() => go('globe')}>A Globe</button>
              <button type="button" aria-pressed={piece === 'ring'} onClick={() => go('ring')}>B Ring</button>
            </div>
          )}
        </div>
      </header>
      <main className="lab-hero" id="top">
        <div className="lp-wrap lab-grid">
          <div className="lab-copy">
            <h1>{hero ? hero.title : ' '}</h1>
            <div className="lab-cta">
              <a className="lp-btn lp-btn-gold gold-metal" href={`/try?lang=${lang}`}>
                <span>{hero ? hero.cta : ' '}</span>
              </a>
            </div>
          </div>
          <Stage />
        </div>
      </main>
    </>
  );
}
