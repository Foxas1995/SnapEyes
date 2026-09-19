import React, { useState } from 'react';
import { Star, Sparkles, Sun, Moon, Lamp, CheckCircle2, ShieldCheck } from 'lucide-react';

export const WallMockupGallery: React.FC = () => {
  const [selectedMockup, setSelectedMockup] = useState<number>(0);
  const [ambientLighting, setAmbientLighting] = useState<'daylight' | 'warm' | 'spotlight'>('spotlight');

  const mockups = [
    {
      id: 'living_room',
      title: 'Living Room Framed Canvas',
      format: '80x80 cm Aluminum Frame',
      subtitle: 'Couple Edition: "Where Our Souls Meet"',
      image: '/assets/mockup_wall_livingroom.jpg',
      stars: 5,
      review: '"We placed this above our living room console. Guests literally freeze when they enter. Unbelievable detail!"',
      author: 'Marcus & Sarah L. — London, UK'
    },
    {
      id: 'acrylic_single',
      title: 'Floating Acrylic Glass',
      format: '50x50 cm Diamond-Polished Acrylic',
      subtitle: 'Single Iris: Deep Obsidian Celestial',
      image: '/assets/mockup_acrylic_single.jpg',
      stars: 5,
      review: '"The 5mm acrylic with chrome standoffs looks like something out of a modern art museum. Worth 10x the price."',
      author: 'David K. — Zurich, Switzerland'
    },
    {
      id: 'bedroom_couple',
      title: 'Panoramic Master Bedroom Canvas',
      format: '120x60 cm Textured Linen Canvas',
      subtitle: 'Couple Duo: Soulmates Cosmic Bridge',
      image: '/assets/mockup_bedroom_couple.jpg',
      stars: 5,
      review: '"The best anniversary gift we have ever created. Having both of our eyes together over our bed is so romantic."',
      author: 'Elena & Matteo — Milan, Italy'
    },
    {
      id: 'pet_human',
      title: 'Scandinavian Natural Oak Frame',
      format: '60x60 cm Solid Oak Wood',
      subtitle: 'Human + Pet Duo: Oliver & Luna 🐾',
      image: '/assets/mockup_pet_human_duo.jpg',
      stars: 5,
      review: "Combining my blue eye with my golden retriever Milo's amber eye brought tears to my eyes. A treasure forever.",
      author: 'Sophie M. & Milo — Berlin, Germany'
    }
  ];

  const current = mockups[selectedMockup];

  // Dynamic Room Lighting CSS Filters
  const getAmbientFilter = () => {
    switch (ambientLighting) {
      case 'daylight':
        return 'brightness(1.05) contrast(1.02) saturate(1.05)';
      case 'warm':
        return 'sepia(0.18) brightness(0.96) contrast(1.05) hue-rotate(-8deg)';
      case 'spotlight':
      default:
        return 'brightness(0.92) contrast(1.15) saturate(1.1)';
    }
  };

  return (
    <section id="wall-gallery" className="py-20 px-4 max-w-7xl mx-auto border-t border-white/5 select-none">
      {/* Title */}
      <div className="text-center max-w-3xl mx-auto mb-10">
        <span className="text-xs font-bold uppercase tracking-widest text-[#f5c542] bg-[#f5c542]/10 border border-[#f5c542]/30 px-4 py-1.5 rounded-full inline-flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>MUSEUM-GRADE LUXURY WALL ART</span>
        </span>
        <h2 className="font-luxury text-3xl sm:text-5xl font-bold mt-4 mb-3">
          FROM SMARTPHONE TO <span className="text-gold-gradient">YOUR LIVING ROOM</span>
        </h2>
        <p className="text-zinc-400 text-xs sm:text-sm max-w-xl mx-auto">
          Our 4K Ultra-HD master files (300 DPI) are calibrated for razor-sharp physical printing up to 120x120 cm on floating acrylic, brushed aluminum, and linen canvas.
        </p>
      </div>

      {/* Interactive Toolbar: Mockup Tabs + Room Ambience Toggle */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8 bg-[#0b0e17] border border-white/10 p-3.5 rounded-2xl max-w-5xl mx-auto shadow-xl">
        {/* Mockup Tabs */}
        <div className="flex flex-wrap justify-center gap-2">
          {mockups.map((m, idx) => (
            <button
              key={m.id}
              onClick={() => setSelectedMockup(idx)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedMockup === idx
                  ? 'bg-[#f5c542] text-black shadow-md shadow-[#f5c542]/25 scale-105'
                  : 'bg-white/5 text-zinc-300 hover:bg-white/10 border border-white/5'
              }`}
            >
              {m.title}
            </button>
          ))}
        </div>

        {/* Room Ambience Lighting Switcher */}
        <div className="flex items-center gap-1.5 bg-black/60 p-1 rounded-xl border border-white/10 text-xs">
          <span className="text-[10px] text-zinc-400 font-mono px-2 uppercase">Ambience:</span>
          <button
            onClick={() => setAmbientLighting('daylight')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold flex items-center gap-1 transition-all ${
              ambientLighting === 'daylight'
                ? 'bg-amber-100 text-black font-bold shadow'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Sun className="w-3 h-3 text-amber-500" />
            <span>Daylight</span>
          </button>
          <button
            onClick={() => setAmbientLighting('warm')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold flex items-center gap-1 transition-all ${
              ambientLighting === 'warm'
                ? 'bg-amber-600 text-white font-bold shadow'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Lamp className="w-3 h-3 text-amber-300" />
            <span>Warm Evening</span>
          </button>
          <button
            onClick={() => setAmbientLighting('spotlight')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold flex items-center gap-1 transition-all ${
              ambientLighting === 'spotlight'
                ? 'bg-[#f5c542] text-black font-bold shadow'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Moon className="w-3 h-3 text-indigo-900" />
            <span>Spotlight</span>
          </button>
        </div>
      </div>

      {/* Hero Showcase Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center bg-[#0a0d16] border border-white/10 p-6 sm:p-8 rounded-3xl shadow-2xl">
        {/* Left: Big Mockup Visual (8 cols) */}
        <div className="lg:col-span-8 group relative rounded-2xl overflow-hidden border border-white/15 shadow-[0_25px_60px_rgba(0,0,0,0.9)] bg-[#04060a]">
          <img
            src={current.image}
            alt={current.title}
            className="w-full h-auto object-cover transition-all duration-700 group-hover:scale-[1.01]"
            style={{ filter: getAmbientFilter() }}
          />

          {/* Dynamic Spotlight Radial Overlay */}
          {ambientLighting === 'spotlight' && (
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'radial-gradient(circle at 50% 40%, transparent 20%, rgba(0,0,0,0.55) 75%)',
              }}
            />
          )}

          {/* Warm Lamp Glow Overlay */}
          {ambientLighting === 'warm' && (
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'radial-gradient(circle at 30% 20%, rgba(251,191,36,0.15) 0%, transparent 60%)',
              }}
            />
          )}

          <div className="absolute top-4 left-4 bg-black/80 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white/15 text-[11px] font-bold text-[#f5c542] flex items-center gap-1.5 shadow-lg">
            <Sparkles className="w-3.5 h-3.5" />
            <span>{current.format}</span>
          </div>
        </div>

        {/* Right: Mockup Details & Review (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div>
            <span className="text-xs font-mono uppercase text-[#f5c542] tracking-wider block mb-1">
              Featured Real Home Installation
            </span>
            <h3 className="font-luxury text-2xl sm:text-3xl font-bold text-white mb-2">
              {current.title}
            </h3>
            <p className="text-sm text-zinc-400 font-serif italic">
              {current.subtitle}
            </p>
          </div>

          {/* Customer Quote Box */}
          <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col gap-3">
            <div className="flex gap-1 text-[#f5c542]">
              {Array.from({ length: current.stars }).map((_, i) => (
                <Star key={i} className="w-4 h-4 fill-[#f5c542]" />
              ))}
            </div>
            <p className="text-xs sm:text-sm text-zinc-200 leading-relaxed font-sans">
              {current.review}
            </p>
            <span className="text-[11px] font-mono text-zinc-400 font-semibold">
              — {current.author}
            </span>
          </div>

          {/* Physical Print Guarantees */}
          <div className="flex flex-col gap-2.5 pt-2 border-t border-white/10 text-xs text-zinc-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>300 DPI Vector PDF & Uncompressed 4K Master Included</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Calibrated for Acrylic Glass, Brushed Metal, & Canvas</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#f5c542] flex-shrink-0" />
              <span>Compatible with Local & Online Print Labs Worldwide</span>
            </div>
          </div>

          <a
            href="#studio"
            className="w-full py-3.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-luxury font-bold text-xs uppercase tracking-widest text-center border border-white/20 transition-all hover:scale-[1.02] active:scale-95 shadow-lg"
          >
            Configure Your Canvas in Studio
          </a>
        </div>
      </div>
    </section>
  );
};
