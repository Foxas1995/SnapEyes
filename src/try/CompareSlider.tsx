import React, { useRef, useState } from 'react';
import { MoveHorizontal } from 'lucide-react';

interface Props {
  before: string;
  after: string;
  beforeLabel?: string;
  afterLabel?: string;
}

/** Before/after slider: both images fill the same square, the "after" layer is clipped at the handle. Works with touch and mouse. */
export const CompareSlider: React.FC<Props> = ({ before, after, beforeLabel = 'Your photo', afterLabel = 'Restored' }) => {
  const [pos, setPos] = useState(50);
  const [dragging, setDragging] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  const update = (clientX: number) => {
    const el = box.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.max(0, Math.min(100, pct)));
  };

  return (
    <div
      ref={box}
      className="relative aspect-square w-full overflow-hidden rounded-2xl bg-black border border-white/10 select-none touch-none cursor-ew-resize"
      onPointerDown={(e) => { setDragging(true); (e.target as Element).setPointerCapture?.(e.pointerId); update(e.clientX); }}
      onPointerMove={(e) => { if (dragging) update(e.clientX); }}
      onPointerUp={() => setDragging(false)}
      onPointerCancel={() => setDragging(false)}
    >
      <img src={before} alt={beforeLabel} className="absolute inset-0 w-full h-full object-cover pointer-events-none" draggable={false} />
      <img
        src={after}
        alt={afterLabel}
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        draggable={false}
        style={{ clipPath: `inset(0 0 0 ${pos}%)` }}
      />
      <span className="absolute top-3 left-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-zinc-200">{beforeLabel}</span>
      <span className="absolute top-3 right-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-[#f5c542]">{afterLabel}</span>
      <div className="absolute top-0 bottom-0 w-0.5 bg-[#f5c542] shadow-[0_0_12px_rgba(245,197,66,0.9)]" style={{ left: `${pos}%` }}>
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-[#f5c542] text-black flex items-center justify-center border-2 border-white shadow-lg">
          <MoveHorizontal className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
