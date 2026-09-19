import React, { useState, useEffect, useRef } from 'react';
import { ArrowDown, Sparkles, Focus, Camera } from 'lucide-react';

export const ScrollyHero: React.FC = () => {
  const [scrollY, setScrollY] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Canvas particle starfield with velocity reactivity
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // 120 cosmic golden stardust particles
    const particles = Array.from({ length: 120 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 1.8 + 0.4,
      alpha: Math.random() * 0.7 + 0.2,
      speedX: (Math.random() - 0.5) * 0.4,
      speedY: (Math.random() - 0.5) * 0.4,
      pulse: Math.random() * Math.PI * 2,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Deep celestial radial gradient in center
      const grad = ctx.createRadialGradient(
        width / 2,
        height / 2,
        40,
        width / 2,
        height / 2,
        Math.min(width, height) * 0.6
      );
      grad.addColorStop(0, 'rgba(245, 197, 66, 0.08)');
      grad.addColorStop(0.45, 'rgba(212, 175, 55, 0.03)');
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Draw floating stardust
      particles.forEach((p) => {
        p.x += p.speedX;
        p.y += p.speedY;
        p.pulse += 0.025;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        const currentAlpha = p.alpha * (0.6 + 0.4 * Math.sin(p.pulse));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 215, 120, ${currentAlpha})`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = 'rgba(245, 197, 66, 0.7)';
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  // Compute scroll progress for 260vh zone (0.00 to 1.00)
  const maxScroll = 1250;
  const progress = Math.min(Math.max(scrollY / maxScroll, 0), 1);

  // Discrete Stage for text captions
  const stage = progress < 0.33 ? 1 : progress < 0.67 ? 2 : 3;

  // CONTINUOUS 3D MATH:
  // Phase 1 (0.0 to 0.40): Camera dive into pupil.
  // Scale grows from 1.0 to 2.4, raw photo skin blurs and expands outwards
  const diveScale = 1.0 + Math.min(progress / 0.40, 1) * 1.4;
  const rawFadeOut = Math.min(Math.max((progress - 0.18) / 0.20, 0), 1);

  // Phase 2 (0.35 to 0.70): Partner eye glides in horizontally with magnetic curve
  const partnerEntry = Math.min(Math.max((progress - 0.38) / 0.22, 0), 1);
  const partnerTranslateX = (1 - partnerEntry) * 80; // 80px to 0px
  const partnerOpacity = partnerEntry;

  // Phase 3 (0.65 to 1.00): Camera pulls back smoothly and mounts into luxury framed acrylic
  const pullBackProgress = Math.min(Math.max((progress - 0.65) / 0.25, 0), 1);
  const frameMountScale = 1.0 - pullBackProgress * 0.12; // subtle pull back
  // frameBorderOpacity removed
  const glassSheenPosition = -100 + pullBackProgress * 250; // -100% to 150% specular sweep

  return (
    <section id="scrolly" className="relative h-[260vh] w-full bg-[#020306] text-white select-none">
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-between py-10 px-4 overflow-hidden">
        
        {/* Canvas starfield */}
        <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none z-0" />

        {/* Dynamic Fluid Headings */}
        <div className="relative z-20 text-center max-w-3xl pt-8 sm:pt-12 h-32 flex flex-col items-center justify-center">
          {stage === 1 && (
            <div className="animate-fade-in transition-all duration-300">
              <h1 className="font-luxury text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight">
                YOUR EYES ARE A <span className="text-gold-gradient">LIVING UNIVERSE.</span>
              </h1>
              <p className="text-zinc-400 text-xs sm:text-sm mt-3 max-w-lg mx-auto">
                Turn any smartphone eye photo into museum-grade 300 DPI cosmic art in seconds.
              </p>
            </div>
          )}

          {stage === 2 && (
            <div className="animate-fade-in transition-all duration-300">
              <h2 className="font-luxury text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight">
                INTO THE <span className="text-gold-gradient">OBSIDIAN VOID.</span>
              </h2>
              <p className="text-amber-200/90 text-xs sm:text-sm mt-3 max-w-lg mx-auto">
                Corneal glare dissolves. 10,000 microscopic crypts meet in a celestial stardust fusion.
              </p>
            </div>
          )}

          {stage === 3 && (
            <div className="animate-fade-in transition-all duration-300">
              <h2 className="font-luxury text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight">
                WHERE OUR <span className="text-gold-gradient">SOULS MEET.</span>
              </h2>
              <p className="text-emerald-300/90 text-xs sm:text-sm mt-3 max-w-lg mx-auto">
                The finished luxury masterpiece. Archival acrylic & fine art canvas for couples, families, & pets.
              </p>
            </div>
          )}
        </div>

        {/* 3D SPATIAL CAMERA STAGE */}
        <div 
          className="relative z-10 my-auto flex items-center justify-center w-full max-w-4xl h-[420px] sm:h-[500px]"
          style={{ perspective: '1200px' }}
        >
          {/* Main 3D Moving Rig */}
          <div
            className="relative flex items-center justify-center transition-transform duration-100 ease-out"
            style={{
              transform: `scale(${stage === 3 ? frameMountScale : diveScale}) rotateX(${(1 - progress) * 3}deg)`,
              transformStyle: 'preserve-3d',
            }}
          >
            {/* Luminous Ambient Stardust Aura behind Canvas */}
            <div
              className="absolute w-[500px] h-[500px] sm:w-[620px] sm:h-[620px] rounded-full pointer-events-none transition-opacity duration-300"
              style={{
                background: 'radial-gradient(circle, rgba(245,197,66,0.32) 0%, rgba(212,175,55,0.12) 40%, transparent 70%)',
                filter: 'blur(45px)',
                opacity: progress > 0.2 ? 1 : progress * 5,
              }}
            />

            {/* ARTWORK DISPLAY FRAME */}
            <div 
              className={`relative overflow-hidden transition-all duration-300 ${
                stage === 3
                  ? 'w-[360px] h-[240px] sm:w-[540px] sm:h-[360px] rounded-2xl shadow-[0_30px_90px_rgba(0,0,0,0.98)] border-2 border-amber-400/40 bg-black'
                  : 'w-64 h-64 sm:w-80 sm:h-80 rounded-3xl shadow-[0_20px_60px_rgba(0,0,0,0.95)] border border-white/20 bg-[#0a0c14]'
              }`}
            >
              {/* SPECULAR GLASS SHEEN OVERLAY (Phase 3 Museum Acrylic Polish) */}
              {stage === 3 && (
                <div 
                  className="absolute inset-0 pointer-events-none z-30 opacity-40 mix-blend-overlay"
                  style={{
                    background: `linear-gradient(115deg, transparent 20%, rgba(255,255,255,0.85) 50%, transparent 80%)`,
                    transform: `translateX(${glassSheenPosition}%)`,
                    transition: 'transform 0.1s linear',
                  }}
                />
              )}

              {/* LAYER 1: Raw Phone Eye Photo (Fades and Expands into center) */}
              <div
                className="absolute inset-0 w-full h-full transition-all duration-200"
                style={{
                  opacity: 1 - rawFadeOut,
                  filter: `blur(${rawFadeOut * 12}px) brightness(${1 - rawFadeOut * 0.3})`,
                  display: rawFadeOut >= 0.99 ? 'none' : 'block',
                }}
              >
                <img
                  src="/assets/sample_eye_blue_1789706902835.jpg"
                  alt="Raw Smartphone Eye"
                  className="w-full h-full object-cover"
                />

                {/* Camera Viewfinder Telemetry HUD */}
                <div 
                  className="absolute inset-3 pointer-events-none flex flex-col justify-between p-2.5 border border-white/25 rounded-2xl transition-opacity duration-200"
                  style={{ opacity: Math.max(0, 1 - rawFadeOut * 3) }}
                >
                  <div className="flex justify-between items-center text-[9px] font-mono text-white/80">
                    <span className="bg-black/70 px-2 py-0.5 rounded backdrop-blur-sm flex items-center gap-1">
                      <Camera className="w-3 h-3 text-[#f5c542]" />
                      SMARTPHONE MACRO
                    </span>
                    <span className="text-emerald-400 font-bold bg-black/70 px-2 py-0.5 rounded flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                      AUTO FOCUS
                    </span>
                  </div>

                  {/* Pulsing Crosshair */}
                  <div className="w-12 h-12 border border-[#f5c542]/70 self-center rounded-full pointer-events-none flex items-center justify-center animate-pulse">
                    <Focus className="w-6 h-6 text-[#f5c542]/80" />
                  </div>

                  <div className="flex justify-between items-center text-[8px] font-mono text-white/60">
                    <span>ISO 100 · F/1.8</span>
                    <span className="text-[#f5c542]">AI DE-GLARING READY</span>
                  </div>
                </div>
              </div>

              {/* LAYER 2: ISOLATED COSMIC IRIS (Solo in Stage 2, Duo in Stage 3) */}
              {rawFadeOut > 0.05 && (
                <div
                  className="absolute inset-0 w-full h-full flex items-center justify-center transition-opacity duration-200"
                  style={{ opacity: rawFadeOut }}
                >
                  {/* If stage 3: Full 2-Eye Duo Artwork with Title & Stardust */}
                  {stage === 3 ? (
                    <div className="relative w-full h-full">
                      <img
                        src="/assets/art_2eyes_celestial_gold_clean.jpg"
                        alt="Where Our Souls Meet - Duo Artwork"
                        className="w-full h-full object-cover"
                      />
                      {/* Acrylic Standoff Chrome Screws in corners */}
                      <div className="absolute top-2.5 left-2.5 w-2.5 h-2.5 rounded-full bg-gradient-to-br from-zinc-200 to-zinc-600 shadow-md border border-white/60" />
                      <div className="absolute top-2.5 right-2.5 w-2.5 h-2.5 rounded-full bg-gradient-to-br from-zinc-200 to-zinc-600 shadow-md border border-white/60" />
                      <div className="absolute bottom-2.5 left-2.5 w-2.5 h-2.5 rounded-full bg-gradient-to-br from-zinc-200 to-zinc-600 shadow-md border border-white/60" />
                      <div className="absolute bottom-2.5 right-2.5 w-2.5 h-2.5 rounded-full bg-gradient-to-br from-zinc-200 to-zinc-600 shadow-md border border-white/60" />
                    </div>
                  ) : (
                    /* Stage 2: Dynamic Duo Convergence in Deep Space */
                    <div className="relative w-full h-full flex items-center justify-center bg-[#05070d]">
                      {/* Eye 1 (Primary blue, centered with stardust) */}
                      <div className="relative w-36 h-36 sm:w-44 sm:h-44 drop-shadow-[0_0_35px_rgba(245,197,66,0.5)]">
                        <img
                          src="/assets/iris_blue_clean.png"
                          alt="Primary Iris"
                          className="w-full h-full object-contain"
                        />
                      </div>

                      {/* Eye 2 (Partner brown iris, glides in with gravity curve) */}
                      <div
                        className="relative w-36 h-36 sm:w-44 sm:h-44 drop-shadow-[0_0_35px_rgba(245,197,66,0.5)] -ml-12 transition-all duration-150"
                        style={{
                          transform: `translateX(${partnerTranslateX}px)`,
                          opacity: partnerOpacity,
                        }}
                      >
                        <img
                          src="/assets/iris_brown_clean.png"
                          alt="Partner Iris"
                          className="w-full h-full object-contain"
                        />
                      </div>

                      {/* Luminous Golden Bridge between them */}
                      <div 
                        className="absolute inset-0 pointer-events-none flex items-center justify-center"
                        style={{ opacity: partnerOpacity }}
                      >
                        <div className="w-24 h-24 bg-gradient-to-r from-amber-400/20 via-amber-300/40 to-amber-400/20 rounded-full filter blur-xl" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Floating Stage Identifier Label */}
          <div className="absolute bottom-2 z-20 text-center">
            <span className="text-[11px] font-luxury font-bold uppercase tracking-widest text-[#f5c542] bg-black/80 px-4 py-1.5 rounded-full border border-[#f5c542]/40 backdrop-blur-md shadow-2xl inline-flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>
                {stage === 1 && '1. Raw Smartphone Flash Photo'}
                {stage === 2 && '2. AI De-glaring & Cosmic Duo Convergence'}
                {stage === 3 && '3. 300 DPI Archival Museum Acrylic Print'}
              </span>
            </span>
          </div>
        </div>

        {/* Scroll Callout Bottom */}
        <div className="relative z-20 flex flex-col items-center pb-2">
          {stage < 3 ? (
            <div className="flex flex-col items-center gap-1.5 text-zinc-400 text-xs animate-bounce">
              <span className="text-[11px] font-mono tracking-widest text-zinc-400">SCROLL TO DIVE INTO THE IRIS</span>
              <ArrowDown className="w-4 h-4 text-[#f5c542]" />
            </div>
          ) : (
            <a
              href="#studio"
              className="bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black font-luxury font-bold text-xs uppercase tracking-widest px-6 py-2.5 rounded-full shadow-lg shadow-[#f5c542]/30 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <span>Create Your Artwork in Studio</span>
              <ArrowDown className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </section>
  );
};
