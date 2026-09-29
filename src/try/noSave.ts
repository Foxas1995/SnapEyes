// The preview images on /try (the restored iris, the artwork, their thumbnails) cannot be dragged out, selected or
// long-pressed: no "Save image" menu on a phone, no context menu on a computer. Belt and braces, because each browser
// honours a different one: the image takes no pointer events (a long press lands on the box around it, which holds no
// image to save), -webkit-touch-callout: none (iOS Safari), and the context menu is cancelled (Android Chrome, desktop).
// A screenshot cannot be blocked on the web, and that is fine: what the page shows is reduced and watermarked
// (api/_lib/preview.py, api/compose.py), and the clean restoration never reaches the page at all.
import type React from 'react';

const stop = (e: React.SyntheticEvent) => e.preventDefault();

/** Inline style of the box around protected images. */
export const NO_SAVE_STYLE: React.CSSProperties = { WebkitTouchCallout: 'none', WebkitUserSelect: 'none', userSelect: 'none' };

/** Inline style of a protected image (a style of its own is merged after it). */
export const NO_SAVE_IMG_STYLE: React.CSSProperties = { ...NO_SAVE_STYLE, pointerEvents: 'none' };

/** Spread on an <img>: <img {...NO_SAVE} src=... />. It takes no clicks: put it inside the button or box that does. */
export const NO_SAVE = { draggable: false, onContextMenu: stop, onDragStart: stop, style: NO_SAVE_IMG_STYLE } as const;

/** Spread on the box around protected images: a long press on the box never opens a menu either. */
export const NO_SAVE_BOX = { onContextMenu: stop, style: NO_SAVE_STYLE } as const;
