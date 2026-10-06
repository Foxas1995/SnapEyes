// One module graph for the market, legal and withdrawal code, so that a market adopted here is the one the links read.
export * as M from '/src/shared/markets.ts';
export * as L from '/src/shared/legal.ts';
export { readWithdrawal } from '/src/order/withdraw.ts';
export { EDITIONS } from '/src/legal/editions.ts';
import en from '/src/landing/copy/en.json';
import de from '/src/landing/copy/de.json';
import lt from '/src/landing/copy/lt.json';
import hu from '/src/landing/copy/hu.json';
export const COPY = { en, de, lt, hu };
