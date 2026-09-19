import React from 'react';
import { Check, X } from 'lucide-react';

export const MarketComparison: React.FC = () => {
  return (
    <section id="comparison" className="py-20 px-4 max-w-6xl mx-auto border-t border-white/5">
      <div className="text-center max-w-3xl mx-auto mb-14">
        <span className="text-xs font-bold uppercase tracking-widest text-[#f5c542] bg-[#f5c542]/10 border border-[#f5c542]/30 px-4 py-1.5 rounded-full">
          TRANSPARENT VALUE COMPARISON
        </span>
        <h2 className="font-luxury text-3xl sm:text-5xl font-bold mt-4 mb-4">
          WHY SNAPEYES IS <span className="text-gold-gradient">IN A LEAGUE OF ITS OWN</span>
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base">
          See why over 12,000 customers switched from physical studios and slow retouching sites to SnapEyes.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[620px]">
          <thead>
            <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-zinc-400">
              <th className="py-4 px-4">Feature</th>
              <th className="py-4 px-4 text-[#f5c542] font-black bg-[#f5c542]/5 rounded-t-xl">
                ✨ SnapEyes.com
              </th>
              <th className="py-4 px-4 text-zinc-400">NuvaIris.com</th>
              <th className="py-4 px-4 text-zinc-400">Eyepic App</th>
              <th className="py-4 px-4 text-zinc-400">Physical Studio (Iris Galerie)</th>
            </tr>
          </thead>
          <tbody className="text-xs divide-y divide-white/5">
            <tr>
              <td className="py-4 px-4 font-semibold text-white">See Watermarked Preview Before Paying</td>
              <td className="py-4 px-4 font-bold text-emerald-400 bg-[#f5c542]/5">
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>YES (Instant in 5 sec)</span>
                </div>
              </td>
              <td className="py-4 px-4 text-rose-400">
                <div className="flex items-center gap-1.5">
                  <X className="w-4 h-4" />
                  <span>NO (Pay $35 blindly first)</span>
                </div>
              </td>
              <td className="py-4 px-4 text-rose-400">
                <div className="flex items-center gap-1.5">
                  <X className="w-4 h-4" />
                  <span>NO ($9.99/wk sub wall)</span>
                </div>
              </td>
              <td className="py-4 px-4 text-zinc-400">Requires physical studio trip</td>
            </tr>

            <tr>
              <td className="py-4 px-4 font-semibold text-white">Turnaround Time</td>
              <td className="py-4 px-4 font-bold text-emerald-400 bg-[#f5c542]/5">
                <span>Instant (30 Seconds)</span>
              </td>
              <td className="py-4 px-4 text-zinc-400">24 – 48 Hours wait</td>
              <td className="py-4 px-4 text-zinc-400">1 – 2 Hours</td>
              <td className="py-4 px-4 text-zinc-400">3 – 7 Days shipping</td>
            </tr>

            <tr>
              <td className="py-4 px-4 font-semibold text-white">Automatic Glare & Reflection Removal</td>
              <td className="py-4 px-4 font-bold text-emerald-400 bg-[#f5c542]/5">
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>Radial Inpainting AI</span>
                </div>
              </td>
              <td className="py-4 px-4 text-zinc-400">Manual retoucher</td>
              <td className="py-4 px-4 text-zinc-400">Blur filter</td>
              <td className="py-4 px-4 text-zinc-400">Studio ring light only</td>
            </tr>

            <tr>
              <td className="py-4 px-4 font-semibold text-white">1 to 8 Eyes & Pet Companions</td>
              <td className="py-4 px-4 font-bold text-emerald-400 bg-[#f5c542]/5">
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>YES (Humans & Pets 🐾)</span>
                </div>
              </td>
              <td className="py-4 px-4 text-zinc-400">Up to 2 only</td>
              <td className="py-4 px-4 text-zinc-400">Single eye only</td>
              <td className="py-4 px-4 text-zinc-400">+€50 per additional eye</td>
            </tr>

            <tr>
              <td className="py-4 px-4 font-semibold text-white">Starting Price</td>
              <td className="py-4 px-4 font-extrabold text-[#f5c542] bg-[#f5c542]/5">
                €19.97 (Clean) / €24.97 (Art)
              </td>
              <td className="py-4 px-4 text-zinc-400">$24.99 – $39.99</td>
              <td className="py-4 px-4 text-zinc-400">$39.99/year subscription</td>
              <td className="py-4 px-4 text-rose-400">€69 – €450+</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
};
