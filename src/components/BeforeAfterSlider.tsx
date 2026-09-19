import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Sparkles, MoveHorizontal, Smartphone, CheckCircle2 } from 'lucide-react';

export const BeforeAfterSlider: React.FC = () => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [activePreset, setActivePreset] = useState<'single' | 'couple'>('couple');
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percent = Math.max(0, Math.min((x / rect.width) * 100, 100));
    setSliderPosition(percent);
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  }, [isDragging, handleMove]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  }, [isDragging, handleMove]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchmove', handleTouchMove);
      window.addEventListener('touchend', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove]);

  const afterImage = activePreset === 'couple'
    ? '/assets/art_2eyes_celestial_gold_clean.jpg'
    : '/assets/art_1eye_celestial_gold_clean.jpg';

  return (
    <section className="py-20 px-4 max-w-6xl mx-auto border-t border-white/5 select-none">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-10">
        <span className="text-xs font-bold uppercase tracking-widest text-[#f5c542] bg-[#f5c542]/10 border border-[#f5c542]/30 px-4 py-1.5 rounded-full inline-flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>INTERACTIVE SPLIT COMPARISON</span>
        </span>
        <h2 className="font-luxury text-3xl sm:text-5xl font-bold mt-4 mb-3">
          SEE THE <span className="text-gold-gradient">METAMORPHOSIS</span>
        </h2>
        <p className="text-zinc-400 text-xs sm:text-sm max-w-xl mx-auto">
          Slide horizontally to see how your everyday phone flash photo transforms into an uncompressed 300 DPI cosmic art piece.
        </p>

        {/* Preset Selector */}
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setActivePreset('single')}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activePreset === 'single'
                ? 'bg-[#f5c542] text-black font-bold shadow-md shadow-[#f5c542]/20'
                : 'bg-white/5 text-zinc-300 hover:bg-white/10 border border-white/10'
            }`}
          >
            1. Solo Iris (Celestial Gold)
          </button>
          <button
            onClick={() => setActivePreset('couple')}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
              activePreset === 'couple'
                ? 'bg-[#f5c542] text-black font-bold shadow-md shadow-[#f5c542]/20'
                : 'bg-white/5 text-zinc-300 hover:bg-white/10 border border-white/10'
            }`}
          >
            2. Couple Duo ("Where Our Souls Meet")
          </button>
        </div>
      </div>

      {/* Interactive Slider Frame */}
      <div className="relative max-w-4xl mx-auto rounded-3xl p-2 bg-gradient-to-b from-white/15 to-white/5 shadow-[0_25px_70px_rgba(0,0,0,0.9)] border border-white/10">
        <div
          ref={containerRef}
          onMouseDown={() => setIsDragging(true)}
          onTouchStart={() => setIsDragging(true)}
          className="relative aspect-[16/10] sm:aspect-[16/9] w-full overflow-hidden rounded-2xl cursor-ew-resize bg-[#07090e]"
        >
          {/* RIGHT LAYER (AFTER): 4K Art Masterpiece (Full Width Base) */}
          <img
            src={afterImage}
            alt="After - 4K Iris Art Masterpiece"
            className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          />

          {/* After Badge */}
          <div className="absolute top-4 right-4 z-10 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-[#f5c542]/40 text-[11px] font-bold text-[#f5c542] flex items-center gap-1.5 shadow-lg">
            <Sparkles className="w-3.5 h-3.5" />
            <span>4K FINISHED ARTWORK (DE-GLARED)</span>
          </div>

          {/* LEFT LAYER (BEFORE): Raw Phone Photo (Clipped via sliderPosition) */}
          <div
            className="absolute inset-0 overflow-hidden pointer-events-none"
            style={{ width: `${sliderPosition}%` }}
          >
            <div className="relative w-full h-full" style={{ width: containerRef.current?.offsetWidth || '100%' }}>
              <img
                src="/assets/sample_eye_blue_1789706902835.jpg"
                alt="Before - Raw Smartphone Photo"
                className="absolute inset-0 w-full h-full object-cover filter brightness-95"
              />

              {/* Smartphone Viewfinder Grid overlay on Before side */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 flex flex-col justify-between p-4">
                <div className="flex justify-between items-center text-[10px] font-mono text-white/80">
                  <span className="bg-black/70 px-2 py-0.5 rounded backdrop-blur-sm flex items-center gap-1">
                    <Smartphone className="w-3 h-3 text-emerald-400" />
                    RAW IPHONE SNAP
                  </span>
                  <span className="text-amber-300 bg-black/70 px-2 py-0.5 rounded">
                    NATURAL GLARE INCLUDED
                  </span>
                </div>
                <div className="text-[10px] font-mono text-white/60">
                  <span>12 MP Macro Mode · Unedited</span>
                </div>
              </div>
            </div>
          </div>

          {/* Before Badge */}
          <div
            className="absolute top-4 left-4 z-10 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 text-[11px] font-bold text-zinc-300 flex items-center gap-1.5 shadow-lg pointer-events-none"
            style={{ opacity: sliderPosition > 15 ? 1 : 0 }}
          >
            <Smartphone className="w-3.5 h-3.5 text-zinc-400" />
            <span>RAW SMARTPHONE PHOTO</span>
          </div>

          {/* DIVIDER LINE WITH GOLD GRIP KNOB */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-[#f5c542] z-20 pointer-events-none shadow-[0_0_15px_rgba(245,197,66,0.8)]"
            style={{ left: `${sliderPosition}%` }}
          >
            {/* Draggable Knob */}
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-gradient-to-br from-[#f5c542] to-[#b3861b] text-black flex items-center justify-center shadow-[0_0_20px_rgba(245,197,66,0.9)] border-2 border-white pointer-events-auto cursor-ew-resize hover:scale-110 active:scale-95 transition-transform">
              <MoveHorizontal className="w-5 h-5 stroke-[2.5]" />
            </div>
          </div>
        </div>

        {/* Micro-Instructions under slider */}
        <div className="flex flex-wrap items-center justify-between text-xs text-zinc-400 px-4 py-3 gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Zero studio visit required · Works with any iPhone / Android camera</span>
          </div>
          <span className="text-[#f5c542] font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Automatic AI Corneal De-glaring
          </span>
        </div>
      </div>
    </section>
  );
};
