// The day's free previews of this connection, as /api/enhance says after each one it makes (api/_lib/previewcap.py left: eight a day per connection). The page
// prints them under the result (./ResultView.tsx) from the first preview on, so nobody meets the ceiling unwarned (the owner, 2026-11-20).
export interface Quota { limit: number; left: number }

/** The server's {limit, left}, or null: nothing is counted there, an older server, or an answer that is not two whole numbers with 0 <= left <= limit. */
export function quotaOf(v: unknown): Quota | null {
  if (!v || typeof v !== 'object') return null;
  const { limit, left } = v as Record<string, unknown>;
  return typeof limit === 'number' && typeof left === 'number' && Number.isInteger(limit) && Number.isInteger(left) && limit > 0 && left >= 0 && left <= limit ? { limit, left } : null;
}
