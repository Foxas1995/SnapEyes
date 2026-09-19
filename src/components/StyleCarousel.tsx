import React from 'react';
import { Sparkles, Check } from 'lucide-react';

export interface StylePreset {
  id: string;
  name: string;
  category: string;
  thumbImage: string;
  accentColor: string;
  desc: string;
}

export const STYLE_PRESETS: StylePreset[] = [
  {
    id: 'celestial_gold',
    name: 'Celestial Gold',
    category: 'Stardust Galaxy',
    thumbImage: '/assets/thumb_celestial_gold.jpg',
    accentColor: '#f5c542',
    desc: 'Golden stardust spiral flowing through cosmic eternity.'
  },
  {
    id: 'gold_kintsugi',
    name: 'Gold Kintsugi',
    category: '24K Liquid Foil',
    thumbImage: '/assets/thumb_gold_kintsugi.jpg',
    accentColor: '#e5b73b',
    desc: 'Flowing ribbons of 24K liquid gold leaf and metallic veins.'
  },
  {
    id: 'deep_nebula',
    name: 'Deep Nebula',
    category: 'James Webb Space',
    thumbImage: '/assets/thumb_deep_nebula.jpg',
    accentColor: '#818cf8',
    desc: 'Bioluminescent cyan and indigo interstellar gas clouds.'
  },
  {
    id: 'obsidian_smoke',
    name: 'Obsidian Smoke',
    category: 'Fluid Charcoal Silk',
    thumbImage: '/assets/thumb_obsidian_smoke.jpg',
    accentColor: '#cbd5e1',
    desc: 'Silken plumes of white and charcoal smoke framing the iris.'
  },
  {
    id: 'solar_corona',
    name: 'Solar Corona',
    category: 'Eclipse Sunburst',
    thumbImage: '/assets/thumb_solar_corona.jpg',
    accentColor: '#fb923c',
    desc: 'Dramatic radial solar flare rays and glowing coronal plasma.'
  },
  {
    id: 'studio_black',
    name: 'Studio Black',
    category: 'Iris Galerie Classic',
    thumbImage: '/assets/thumb_studio_black.jpg',
    accentColor: '#d4af37',
    desc: 'Pure matte museum obsidian. 100% focus on pure iris anatomy.'
  }
];

interface Props {
  selectedStyle: string;
  onSelect: (id: string) => void;
}

export const StyleCarousel: React.FC<Props> = ({ selectedStyle, onSelect }) => {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#f5c542]" />
          <span>Choose Artistic Style (Click to Adapt Canvas)</span>
        </label>
        <span className="text-[10px] text-zinc-400">6 Distinct Art Mediums</span>
      </div>

      {/* Visual Thumbnail Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {STYLE_PRESETS.map((preset) => {
          const isSelected = selectedStyle === preset.id;
          return (
            <button
              key={preset.id}
              onClick={() => onSelect(preset.id)}
              className={`group relative rounded-xl overflow-hidden border text-left transition-all p-1 bg-[#06080e] ${
                isSelected
                  ? 'border-[#f5c542] ring-2 ring-[#f5c542] shadow-[0_0_20px_rgba(245,197,66,0.35)] scale-[1.02]'
                  : 'border-white/10 hover:border-white/30 hover:scale-[1.01]'
              }`}
            >
              {/* Visual Thumbnail Image */}
              <div className="relative aspect-[16/11] rounded-lg overflow-hidden bg-black">
                <img
                  src={preset.thumbImage}
                  alt={preset.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />

                {/* Dark gradient overlay for title legibility */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/25 to-transparent" />

                {/* Checkmark Badge */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#f5c542] text-black flex items-center justify-center text-xs font-black shadow-md">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}

                {/* Title & Category on Image */}
                <div className="absolute bottom-2 left-2 right-2">
                  <span
                    className="text-[9px] uppercase tracking-wider font-bold block"
                    style={{ color: preset.accentColor }}
                  >
                    {preset.category}
                  </span>
                  <span className="text-xs font-bold text-white block truncate leading-tight">
                    {preset.name}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
