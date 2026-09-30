import { useCallback, useRef, useSyncExternalStore, type ButtonHTMLAttributes, type ImgHTMLAttributes, type KeyboardEvent, type ReactNode, type Ref, type RefObject } from 'react';
import { flushSync } from 'react-dom';
import { ArrowRight, Plus } from 'lucide-react';
import { tryUrl } from './config';
import { useLang } from './lang';
import { useCopy } from './copy/useCopy';

export function Eyebrow({ children, center = false }: { children: ReactNode; center?: boolean }) {
  return (
    <p className={`flex items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f5c542] ${center ? 'justify-center' : ''}`}>
      <span aria-hidden="true" className="h-px w-7 bg-[#f5c542]/60" />
      <span>{children}</span>
    </p>
  );
}

export function SectionHead({ eyebrow, title, intro, center = false }: { eyebrow: string; title: string; intro?: string; center?: boolean }) {
  return (
    <div className={center ? 'mx-auto max-w-2xl text-center' : 'max-w-2xl'}>
      <Eyebrow center={center}>{eyebrow}</Eyebrow>
      <h2 className="mt-4 font-luxury text-[28px] leading-[1.15] font-semibold text-white sm:text-[40px] text-balance">{title}</h2>
      {intro && <p className="mt-4 text-[15px] leading-relaxed text-zinc-400 sm:text-base">{intro}</p>}
    </div>
  );
}

// The one primary action on the page: straight to the capture tool. min-h, not a fixed height: on a 320 px
// screen a long German label may still need two lines, and then the pill grows instead of clipping it.
export function CtaLink({ label, full = false, ref }: { label: string; full?: boolean; ref?: Ref<HTMLAnchorElement> }) {
  const { lang } = useLang();
  return (
    <a
      ref={ref}
      href={tryUrl(lang)}
      className={`group inline-flex min-h-[52px] items-center justify-center gap-2.5 rounded-full bg-[#f5c542] px-6 py-3 text-center text-[15px] leading-tight font-semibold tracking-[0.01em] text-[#030408] shadow-[0_10px_40px_-12px_rgba(245,197,66,0.55)] transition-colors hover:bg-[#ffd666] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#f5c542] max-[359px]:px-4 max-[359px]:text-[14px] sm:px-7 ${full ? 'w-full' : ''}`}
    >
      <span>{label}</span>
      <ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5" />
    </a>
  );
}

// A quiet line under a call to action (t.ctaNote). Renders nothing when empty, as it is in both languages today.
export function CtaNote({ text, className = '' }: { text: string; className?: string }) {
  if (!text) return null;
  return <p className={`text-[13px] leading-relaxed text-zinc-400 ${className}`}>{text}</p>;
}

// href: the landing links to its own top; the legal pages link home.
export function Logo({ tag, href = '#top' }: { tag: string; href?: string }) {
  return (
    <a href={href} className="flex items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#f5c542]" aria-label="SnapEyes Private Atelier">
      <svg aria-hidden="true" viewBox="0 0 32 32" className="h-8 w-8 shrink-0">
        <circle cx="16" cy="16" r="15" fill="none" stroke="#f5c542" strokeOpacity="0.55" strokeWidth="1" />
        <circle cx="16" cy="16" r="9.5" fill="none" stroke="#f5c542" strokeWidth="1.4" />
        <circle cx="16" cy="16" r="4" fill="#f5c542" />
      </svg>
      <span className="flex flex-col leading-none">
        <span className="font-luxury text-[17px] font-semibold tracking-[0.18em] text-white">SNAPEYES</span>
        <span className="mt-1 text-[9px] font-medium uppercase tracking-[0.34em] text-zinc-400">{tag}</span>
      </span>
    </a>
  );
}

// ================================================================================================================
// Shared primitives of the new landing (BUILD_PLAN section 2, "Shared"). They are MARKUP: the look comes from the
// landing's own stylesheet (src/landing/css, every rule inside @layer landing and every class prefixed lp-), so they
// carry exactly those class names and no utility classes (a Tailwind utility would outrank the layer and break the
// contextual rules such as .lp-tile-img .lp-vis-chip or .lp-final-chip). They read the page's words from the copy layer
// (src/landing/copy), so they work inside <CopyProvider> only.
// ================================================================================================================

/** The two labels that keep every picture honest (BUILD_PLAN section 7): "example" (DE "Beispiel") for real engine
 *  artwork, "vis" ("AI visualisation", DE "KI-Visualisierung") for every wall, room, hand, desk, phone and edge picture.
 *  The words are the copy's (example.chip, example.vis). */
export type ChipVariant = 'example' | 'vis';

export interface ExampleChipProps {
  variant: ChipVariant;
  /** "example" only: the chip that names a photo of someone else's eye (example.photo, "Example photo"), styled .lp-photo. */
  photo?: boolean;
  /** Other words for the label, from the copy (hero.chipTitle, final.chip): never typed in a component. */
  label?: string;
  /** A second line under the label: the framed chip of the first screen ("You receive the digital file. Printing is not
   *  included."), class lp-frame-chip. Needs the variant "vis". */
  body?: string;
  /** Context classes of the page's CSS (lp-final-chip): where and how this chip sits on its picture. */
  className?: string;
}

/** The label on a picture: <span class="lp-vis-chip">AI visualisation</span> (absolute in the picture's corner by the CSS),
 *  <span class="lp-chip-ex">Example</span> (inline; the tile CSS pins it), or the framed one with a body. */
export function ExampleChip({ variant, photo = false, label, body, className = '' }: ExampleChipProps) {
  const { c } = useCopy();
  const text = label ?? (variant === 'vis' ? c.example.vis : photo ? c.example.photo : c.example.chip);
  if (body !== undefined) {
    return (
      <div data-chip={variant} className={`lp-frame-chip ${className}`.trim()}>
        <b>{text}</b>
        <span>{body}</span>
      </div>
    );
  }
  const cls = variant === 'vis' ? 'lp-vis-chip' : photo ? 'lp-chip-ex lp-photo' : 'lp-chip-ex';
  return (
    <span data-chip={variant} className={`${cls} ${className}`.trim()}>
      {text}
    </span>
  );
}

type PillRole = 'radio' | 'tab';

export interface PillProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'role' | 'disabled'> {
  /** radio: a member of a role="radiogroup"; tab: a member of a role="tablist"; left out: a toggle button. */
  role?: PillRole;
  /** selected, checked or pressed, whichever the role means. */
  on?: boolean;
  /** dimmed and ignored by clicks and by the arrow keys (aria-disabled: it stays in the page for a screen reader). */
  disabled?: boolean;
}

/** A pill button (.lp-pill). The state attribute is the one the role wants (aria-checked for a radio, aria-selected for a
 *  tab, aria-pressed for a toggle) and the CSS styles the attribute. In a radio or tab role the roving tabindex is the
 *  default: the selected pill is the tab stop (0), the others are reached with the arrow keys (-1, see useRoving). Pass
 *  tabIndex to decide otherwise. */
export function Pill({ role, on = false, disabled = false, type = 'button', tabIndex, className = '', onClick, children, ...rest }: PillProps) {
  const state = role === 'radio' ? { 'aria-checked': on } : role === 'tab' ? { 'aria-selected': on } : { 'aria-pressed': on };
  return (
    <button
      {...rest}
      {...state}
      type={type}
      role={role}
      tabIndex={tabIndex ?? (role ? (on ? 0 : -1) : undefined)}
      aria-disabled={disabled || undefined}
      onClick={(e) => {
        if (disabled) e.preventDefault();
        else onClick?.(e);
      }}
      className={`lp-pill ${className}`.trim()}
    >
      {children}
    </button>
  );
}

/** Re-render a group, then put the focus back on the same control. A render that replaces the control the visitor just
 *  used (other keys, another element) would drop the focus to the page; this keeps it where they were. Stable keys are
 *  still the first defence (a node that is not remounted keeps its focus by itself), this is the second.
 *    const keepFocus = useKeepFocus(groupRef);
 *    keepFocus(() => setTab(next), `[data-tab="${next}"]`);      // selector below the group, or a function giving the node
 *  The update runs synchronously (flushSync), so the node is there when it is looked for. Only when the focus was inside
 *  the group before the update is it moved; a click elsewhere never steals it. */
export function useKeepFocus(root: RefObject<HTMLElement | null>) {
  return (update: () => void, find: string | (() => HTMLElement | null)) => {
    const el = root.current;
    const had = !!el && el.contains(document.activeElement);
    flushSync(update);
    if (!had) return;
    const node = typeof find === 'string' ? root.current?.querySelector<HTMLElement>(find) : find();
    if (node && node !== document.activeElement) node.focus({ preventScroll: true });
  };
}

const ROVING_ITEMS = '[role=tab],[role=radio]';

/** Arrow keys, Home and End move between the tabs or radios of one group, and the one reached is picked (selection follows
 *  focus, as in the prototype). The group element takes ref and onKeyDown; the items are the role="tab" and role="radio"
 *  children (or the selector you pass), and an item with aria-disabled="true" is skipped. Alt, Ctrl and Meta combinations
 *  are left to the browser (Alt+Left is "back").
 *    const roving = useRoving<HTMLDivElement>((el) => setEye(el.dataset.eye as EyeId));
 *    <div ref={roving.ref} onKeyDown={roving.onKeyDown} role="radiogroup">...</div> */
export function useRoving<T extends HTMLElement = HTMLElement>(onPick: (item: HTMLElement, index: number) => void, selector: string = ROVING_ITEMS) {
  const ref = useRef<T>(null);
  const onKeyDown = useCallback(
    (e: KeyboardEvent<T>) => {
      const root = ref.current;
      if (!root || e.altKey || e.ctrlKey || e.metaKey) return;
      const items = Array.from(root.querySelectorAll<HTMLElement>(selector)).filter((x) => x.getAttribute('aria-disabled') !== 'true');
      const i = items.indexOf(document.activeElement as HTMLElement);
      if (i < 0) return;
      let j = -1;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') j = (i + 1) % items.length;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') j = (i - 1 + items.length) % items.length;
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = items.length - 1;
      if (j < 0) return;
      e.preventDefault();
      items[j].focus();
      onPick(items[j], j);
    },
    [onPick, selector],
  );
  return { ref, onKeyDown };
}

/** A CSS media query as a boolean that follows the window (the privacy list is plain text from 960 px and a disclosure on
 *  phones; the size guide draws another view box under 640 px). serverValue is what a render without a window says. */
export function useMediaQuery(query: string, serverValue = false): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const mq = window.matchMedia(query);
      mq.addEventListener('change', onChange);
      return () => mq.removeEventListener('change', onChange);
    },
    [query],
  );
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches, () => serverValue);
}

export interface DisclosureProps {
  /** The always visible line (the question, the title). A plus icon follows it and the CSS turns it into a cross when open. */
  summary: ReactNode;
  children: ReactNode;
  /** Open on first render; the visitor's own toggling is kept by the browser afterwards (uncontrolled). */
  defaultOpen?: boolean;
  /** Controlled: open follows this, and onToggle reports the visitor's toggling (keep the two in step). */
  open?: boolean;
  onToggle?: (open: boolean) => void;
  id?: string;
  /** The page's class for this kind of disclosure (lp-qa for the FAQ, lp-tips, lp-pv, lp-more, lp-compare): its CSS styles
   *  the summary row, the marker and the plus icon (details.lp-qa summary svg ...). */
  className?: string;
  summaryClassName?: string;
  iconClassName?: string;
}

/** The page's one disclosure: a native <details>, so the keyboard (Enter, Space), the screen reader's "expanded" state, find
 *  in page and opening by a #link all work without any script. The plus icon is the prototype's (two strokes, stroke 2.2),
 *  hidden from screen readers. Give it a stable key so an open item stays open when the language changes. */
export function Disclosure({ summary, children, defaultOpen, open, onToggle, id, className = '', summaryClassName = '', iconClassName = '' }: DisclosureProps) {
  return (
    <details id={id} open={open ?? defaultOpen} onToggle={onToggle ? (e) => onToggle(e.currentTarget.open) : undefined} className={className || undefined}>
      <summary className={summaryClassName || undefined}>
        {summary}
        <Plus aria-hidden="true" strokeWidth={2.2} className={iconClassName || undefined} />
      </summary>
      {children}
    </details>
  );
}

/** What a picture needs to know about its file: the address, an optional srcset, and the intrinsic size (width and height
 *  reserve the space, so the page does not jump). This is what asset(name) of src/landing/assets.ts returns (the asset
 *  manifest, built with the pictures); Picture takes the result, so it never reads the manifest itself. */
export interface PictureAsset { src: string; srcset?: string; w: number; h: number }

type ImgExtras = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src' | 'srcSet' | 'sizes' | 'width' | 'height' | 'alt' | 'loading' | 'fetchPriority' | 'className'>;

export interface PictureProps {
  asset: PictureAsset;
  alt: string;
  /** The label this picture carries, inside its frame. REQUIRED, so leaving it out is a compile error and a picture without
   *  a label is a decision someone wrote down: 'vis' (AI visualisation), 'example' (real engine artwork) or 'none' (a screen
   *  detail that shows no print, no room and no example: the phone mock-ups, the file card). */
  chip: ChipVariant | 'none';
  /** "example" only: label the chip "Example photo" (a photo of someone else's eye). */
  photo?: boolean;
  /** What the picture says about its width, for the srcset: "(min-width: 960px) 500px, 100vw". */
  sizes?: string;
  /** The first-screen picture: loaded at once with high priority (the LCP image); everything else loads lazily. */
  priority?: boolean;
  /** The frame's class (lp-tile-img, lp-edge-img ...): it must make the frame position: relative, as every frame class of
   *  the landing CSS does, because the chip is pinned inside it. */
  className?: string;
  imgClassName?: string;
  imgProps?: ImgExtras;
  /** Other layers of the same frame, after the chip (a glint, a second image for a cross fade). */
  children?: ReactNode;
}

/** A picture with its label: the image (srcset and sizes from the asset manifest, width and height against layout shift,
 *  lazy unless it is the first screen) and the ExampleChip inside its frame. */
export function Picture({ asset, alt, chip, photo, sizes, priority = false, className = '', imgClassName = '', imgProps, children }: PictureProps) {
  return (
    <div data-chip-area={chip} className={`lp-pic ${className}`.trim()}>
      <img
        {...imgProps}
        src={asset.src}
        srcSet={asset.srcset}
        sizes={asset.srcset ? sizes : undefined}
        width={asset.w}
        height={asset.h}
        alt={alt}
        loading={priority ? undefined : 'lazy'}
        fetchPriority={priority ? 'high' : undefined}
        decoding="async"
        className={imgClassName || undefined}
      />
      {chip !== 'none' && <ExampleChip variant={chip} photo={photo} />}
      {children}
    </div>
  );
}

/** Wraps a printed price, or a sentence holding one, until the server's first answer about the prices has arrived
 *  (useLandingPrices().pending): invisible and out of the accessibility tree, but still taking its space, so a visitor in
 *  a price experiment never sees the standard price for a moment and nothing shifts when the price appears. */
export function PriceGate({ pending, children, className }: { pending: boolean; children: ReactNode; className?: string }) {
  return (
    <span aria-hidden={pending || undefined} className={className} style={pending ? { opacity: 0, userSelect: 'none' } : undefined}>
      {children}
    </span>
  );
}
