// The longest side, in pixels, of the crop of the eye this page cuts from the visitor's photo and sends for the restoration (TryApp process: the
// crop is drawn from the full photo and scaled down only when the iris region is larger than this). One number for the cut and for the sentence that
// tells the visitor about it (copy.ts result.did.quality). It lives here and not in the copy: a number in the copy files that equals a price in Stripe's
// smallest unit is read as a written price by scripts/check_prices.mjs.
export const CROP_MAX_PX = 1400;
