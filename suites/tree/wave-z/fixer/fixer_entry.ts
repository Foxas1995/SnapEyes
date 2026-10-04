// One module graph for the market, legal and withdrawal code, so that a market adopted here is the one the links read.
export * as M from '/src/shared/markets.ts';
export * as L from '/src/shared/legal.ts';
export { readWithdrawal } from '/src/order/withdraw.ts';
export { EDITIONS } from '/src/legal/editions.ts';
export { COPY } from '/src/landing/copy.ts';
