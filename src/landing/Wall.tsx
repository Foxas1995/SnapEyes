// The wall chapter (#wall): "See your file on a wall". A stage with an AI visualisation of the file in a room, a list of six
// materials (each in its own room), four artworks, what each material is, a compare table, the honest footnote and a text
// link to /try, then the size guide and "More ways to see it". The visitor buys a DIGITAL file: every picture here is an AI
// visualisation and says so in the picture (the chip), and the sentence under the title says printing is not part of the order.
//
// Keyboard: the materials are a vertical tab list and the artworks a radio group, both with a roving tabindex (one tab stop
// each; arrow keys, Home and End move AND pick, as the prototype does), and the focus stays on the control after a pick.
import { useState, type SyntheticEvent } from 'react';
import { asset } from './assets';
import { WALL_THUMBS } from './assets.data';
import { CompareTable } from './CompareTable';
import { MoreRooms } from './MoreRooms';
import { SizeGuide } from './SizeGuide';
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';
import { useKeepFocus, useRoving } from './ui';
import { WallStage } from './WallStage';
import { ARTS, DEFAULT_ART, DEFAULT_MATERIAL, MATERIALS, artFor, glintFor, hasScene, isSized, stagePicture, warm, type Material, type WallArt } from './wallScenes';

export function Wall() {
  const { c, t, lang } = useCopy();
  const w = c.wall;
  const tryHref = useTryHref();
  const [mat, setMat] = useState<Material>(DEFAULT_MATERIAL);
  const [art, setArt] = useState<WallArt>(DEFAULT_ART);

  const matRoving = useRoving<HTMLDivElement>((el) => pickMat(el.dataset.m as Material));
  const artRoving = useRoving<HTMLDivElement>((el) => pickArt(el.dataset.a as WallArt));
  const keepMat = useKeepFocus(matRoving.ref);
  const keepArt = useKeepFocus(artRoving.ref);

  function pickMat(m: Material) {
    keepMat(() => {
      setMat(m);
      setArt(artFor(m, art));
    }, `[data-m="${m}"]`);
    // the tab list scrolls sideways on a phone: bring the picked tab into view
    if (window.innerWidth < 960) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      matRoving.ref.current?.querySelector<HTMLElement>(`[data-m="${m}"]`)?.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
    }
  }
  function pickArt(a: WallArt) {
    if (!hasScene(mat, a)) return;
    keepArt(() => setArt(a), `[data-a="${a}"]`);
  }

  // one material is warmed on hover, focus or touch, never all of them on idle
  const warmFrom = (e: SyntheticEvent) => {
    const b = (e.target as Element).closest?.('[data-m]') as HTMLElement | null;
    if (b) warm(b.dataset.m as Material, art, lang);
  };

  const m = w.materials[mat];
  const pic = stagePicture(mat, art, lang);
  const caption = pic?.sizeOk && isSized(mat) ? t(`wall.captionsSize.${mat}`, { size: c.facts.printMaxCm }) : t(`wall.captions.${mat}`);
  const alt = `${c.example.vis}. ${caption} ${w.arts[art]}.`;

  return (
    <section className="lp-sec lp-wall" id="wall" aria-labelledby="wallH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{w.eyebrow}</p>
          <h2 id="wallH">{w.title}</h2>
        </div>
        <div className="lp-note-box">
          <strong>{w.intro}</strong>
          <span>{w.varies}</span>
        </div>

        <div className="lp-wall-grid">
          <div className="lp-stage-col">
            <WallStage
              picture={pic}
              alt={alt}
              glint={glintFor(mat, art)}
              label={w.stageLabel}
              caption={caption}
              eyesNote={art === 'family4' || art === 'collision' ? w.eyesNote : undefined}
            />
          </div>
          <div className="lp-ctl">
            <p className="lp-ctl-h lp-mat-h" id="matH">{w.materialsLabel}</p>
            <div
              ref={matRoving.ref}
              onKeyDown={matRoving.onKeyDown}
              onPointerOver={warmFrom}
              onFocus={warmFrom}
              onPointerDown={warmFrom}
              onTouchStart={warmFrom}
              className="lp-mats"
              id="mats"
              role="tablist"
              aria-labelledby="matH"
              aria-orientation="vertical"
            >
              {MATERIALS.map((k) => (
                <button
                  key={k}
                  type="button"
                  className="lp-mat"
                  role="tab"
                  id={`mat-${k}`}
                  aria-selected={k === mat}
                  aria-controls="specs"
                  tabIndex={k === mat ? 0 : -1}
                  data-m={k}
                  onClick={() => pickMat(k)}
                >
                  <span className="lp-mn">{w.materials[k].n}</span>
                  <span className="lp-mt">{w.materials[k].tag}</span>
                </button>
              ))}
            </div>
            <div className="lp-specs" id="specs" role="tabpanel" aria-live="polite" aria-labelledby={`mat-${mat}`}>
              <h3>{m.n}</h3>
              <ul>
                {m.facts.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              {mat !== 'phone' && mat !== 'block' && <p className="lp-typ">{w.typical}</p>}
            </div>
            <div className="lp-arts">
              <p className="lp-ctl-h" id="artH">{w.artLabel}</p>
              <div ref={artRoving.ref} onKeyDown={artRoving.onKeyDown} className="lp-pills" id="arts" role="radiogroup" aria-labelledby="artH" style={{ marginTop: 0 }}>
                {ARTS.map((a) => {
                  const thumb = asset(WALL_THUMBS[a]);
                  return (
                    <button
                      key={a}
                      type="button"
                      className="lp-artchip"
                      role="radio"
                      aria-checked={a === art}
                      aria-disabled={!hasScene(mat, a)}
                      tabIndex={a === art ? 0 : -1}
                      data-a={a}
                      onClick={() => pickArt(a)}
                    >
                      <img src={thumb.src} width={thumb.w} height={thumb.h} alt="" loading="lazy" />
                      {w.arts[a]}
                    </button>
                  );
                })}
              </div>
            </div>
            <CompareTable />
          </div>
        </div>

        <p className="lp-fine lp-wall-foot">{w.footnote}</p>
        <p className="lp-wall-cta">
          <a className="lp-link-gold" href={tryHref}>{w.cta}</a>
        </p>

        <SizeGuide />
        <MoreRooms />
      </div>
    </section>
  );
}

export default Wall;
