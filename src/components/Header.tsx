import React, { useState, useEffect } from 'react';
import { Sparkles, Eye, Menu, X } from 'lucide-react';

export const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#07090e]/90 backdrop-blur-xl border-b border-white/10 py-3 shadow-2xl'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between">
        {/* Brand Logo */}
        <a href="#" className="flex items-center gap-2 group">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#f5c542] via-amber-500 to-amber-200 p-[1px] shadow-[0_0_20px_rgba(245,197,66,0.35)] group-hover:shadow-[0_0_30px_rgba(245,197,66,0.6)] transition-all">
            <div className="w-full h-full rounded-full bg-[#07090e] flex items-center justify-center">
              <Eye className="w-4 h-4 text-[#f5c542] group-hover:scale-110 transition-transform" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="font-luxury font-black text-xl tracking-wider text-white">
              SNAP<span className="text-gold-gradient">EYES</span>
            </span>
            <span className="text-[9px] uppercase tracking-widest text-zinc-400 font-medium -mt-1">
              Cosmic Iris Art Studio
            </span>
          </div>
        </a>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-7 text-xs font-semibold uppercase tracking-wider text-zinc-300">
          <a href="#scrolly" className="hover:text-[#f5c542] transition-colors">The Journey</a>
          <a href="#studio" className="hover:text-[#f5c542] transition-colors">Interactive Studio</a>
          <a href="#how-it-works" className="hover:text-[#f5c542] transition-colors">Photo Guide</a>
          <a href="#wall-gallery" className="hover:text-[#f5c542] transition-colors">Wall Gallery</a>
          <a href="#comparison" className="hover:text-[#f5c542] transition-colors">Why Us</a>
          <a href="#studio" className="hover:text-amber-300 flex items-center gap-1 transition-colors text-amber-400">
            <span>🐾 Pet Edition</span>
          </a>
        </nav>

        {/* Right Action */}
        <div className="flex items-center gap-3">
          <a
            href="#studio"
            className="hidden sm:inline-flex items-center gap-2 bg-gradient-to-r from-[#f5c542] via-[#e5b73b] to-[#c99a2e] text-black font-extrabold text-xs uppercase tracking-wider px-5 py-2.5 rounded-full shadow-[0_0_20px_rgba(245,197,66,0.25)] hover:shadow-[0_0_30px_rgba(245,197,66,0.5)] hover:scale-105 active:scale-95 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 fill-current" />
            <span>Try Free in 5s</span>
          </a>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-zinc-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#0a0d16] border-b border-white/10 px-6 py-6 flex flex-col gap-4 text-sm font-semibold tracking-wider">
          <a
            href="#scrolly"
            onClick={() => setMobileMenuOpen(false)}
            className="text-zinc-300 hover:text-[#f5c542]"
          >
            The Journey
          </a>
          <a
            href="#studio"
            onClick={() => setMobileMenuOpen(false)}
            className="text-zinc-300 hover:text-[#f5c542]"
          >
            Interactive Studio (1-8 Eyes)
          </a>
          <a
            href="#how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="text-zinc-300 hover:text-[#f5c542]"
          >
            Smartphone Photo Guide
          </a>
          <a
            href="#wall-gallery"
            onClick={() => setMobileMenuOpen(false)}
            className="text-zinc-300 hover:text-[#f5c542]"
          >
            Wall Mockup Gallery
          </a>
          <a
            href="#comparison"
            onClick={() => setMobileMenuOpen(false)}
            className="text-zinc-300 hover:text-[#f5c542]"
          >
            SnapEyes vs Competitors
          </a>
          <a
            href="#studio"
            onClick={() => setMobileMenuOpen(false)}
            className="mt-2 bg-[#f5c542] text-black text-center py-3 rounded-xl font-bold uppercase tracking-wider text-xs"
          >
            Try Free Now
          </a>
        </div>
      )}
    </header>
  );
};
