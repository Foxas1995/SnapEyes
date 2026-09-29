// A plain HTML bar chart for one daily series (no chart library): thin bars on a baseline, a recessive grid at the
// top value and half of it, and a readout line that names the day and value under the pointer (or the tapped bar;
// the latest day by default). One series, so no legend: the title names it. The same numbers are in the table
// on the statistics page.
import { useState } from 'react';
import type React from 'react';

export interface Bar { label: string; value: number }

export const BarChart: React.FC<{ title: string; bars: Bar[]; format?: (v: number) => string; note?: string }> = ({ title, bars, format = (v) => String(v), note }) => {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(0, ...bars.map((b) => b.value));
  const top = max > 0 ? max : 1;
  const shown = hover ?? bars.length - 1;
  const cur = bars[shown];
  const total = bars.reduce((s, b) => s + b.value, 0);
  return (
    <figure className="bg-[#0b0e17] border border-white/10 rounded-2xl p-4 min-w-0">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 mb-2">
        <span className="text-sm font-bold text-white">{title}</span>
        <span className="text-xs text-white/60">iš viso {format(total)}{note ? ` · ${note}` : ''}</span>
      </figcaption>
      {/* the top value sits in its own row above the plot (pt-4), apart from the caption's total above it */}
      <div className="relative pt-4">
        <span aria-hidden className="absolute right-0 top-0 h-4 leading-4 text-[10px] text-white/45">{format(max)}</span>
        <div className="relative h-32" onMouseLeave={() => setHover(null)}>
          <div aria-hidden className="absolute inset-x-0 top-0 border-t border-dashed border-white/10" />
          <div aria-hidden className="absolute inset-x-0 top-1/2 border-t border-dashed border-white/[0.07]" />
          <div className="absolute inset-0 flex items-end gap-[2px]" role="list" aria-label={title}>
            {bars.map((b, i) => (
              <button
                type="button"
                role="listitem"
                key={b.label}
                aria-label={`${b.label}: ${format(b.value)}`}
                className="relative flex-1 min-w-0 h-full flex items-end focus:outline-none group"
                onMouseEnter={() => setHover(i)}
                onFocus={() => setHover(i)}
                onClick={() => setHover(i)}
              >
                <span
                  className={`block w-full rounded-t-[4px] ${i === shown ? 'bg-[#ffd976]' : 'bg-[#f5c542]/80 group-hover:bg-[#ffd976]'}`}
                  style={{ height: b.value > 0 ? `max(2px, ${(b.value / top) * 100}%)` : '0px' }}
                />
              </button>
            ))}
          </div>
          <div aria-hidden className="absolute inset-x-0 bottom-0 border-t border-white/25" />
        </div>
      </div>
      <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs">
        <span className="text-white/50">{bars[0]?.label}</span>
        <span className="text-white/90 font-semibold">{cur ? `${cur.label}: ${format(cur.value)}` : ''}</span>
        <span className="text-white/50">{bars[bars.length - 1]?.label}</span>
      </div>
    </figure>
  );
};
