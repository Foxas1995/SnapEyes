import React, { useState } from 'react';
import { Check, X, Copy, CheckCheck, Video } from 'lucide-react';

export const PhotoGuide: React.FC = () => {
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [activeTab, setActiveTab] = useState<'human' | 'pet' | 'veo'>('human');

  const veoPrompt = `Create a 15-second vertical 9:16 UGC-style phone tutorial video featuring an authentic 25-year-old creator demonstrating how to photograph an eye for custom iris artwork with an iPhone.

CHARACTER + PRODUCT CONSISTENCY:
Keep the creator's natural look, cozy sunlit room, genuine expression. Natural handheld camera motion, authentic iPhone screen recordings and real skin textures. No commercial studio gloss.

0:00-0:03 — THE HOOK:
Creator speaks naturally to camera: "Stop paying €150 for iris photo studios! You can do this on your iPhone in 10 seconds."

0:03-0:07 — THE LIGHTING & DISTANCE:
Close-up over-the-shoulder shot. Creator turns on flashlight, holds it at a 45-degree angle beside her face. Holds iPhone camera 10cm from her eye. The screen shows the iris in razor-sharp macro clarity.

0:07-0:11 — THE SNAP & UPLOAD:
Creator taps the screen to focus on the iris and snaps the photo. Uploads it directly to SnapEyes.com on mobile Safari. The screen instantly generates a glowing watermarked celestial preview in 5 seconds.

0:11-0:15 — THE REVEAL & CTA:
Creator gasps with excitement, showing the phone screen with the finished cosmic artwork: "Look at the golden fibers! Try yours for free right now at SnapEyes.com."`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(veoPrompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2500);
  };

  return (
    <section id="how-it-works" className="py-20 px-4 max-w-7xl mx-auto border-t border-white/5">
      {/* Title */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <span className="text-xs font-bold uppercase tracking-widest text-[#f5c542] bg-[#f5c542]/10 border border-[#f5c542]/30 px-4 py-1.5 rounded-full">
          ZERO GUESSWORK · 100% SMARTPHONE COMPATIBLE
        </span>
        <h2 className="font-luxury text-3xl sm:text-5xl font-bold mt-4 mb-4">
          HOW TO TAKE THE <span className="text-gold-gradient">PERFECT EYE PHOTO</span>
        </h2>
        <p className="text-zinc-400 text-sm sm:text-base leading-relaxed">
          No expensive macro camera needed. Any modern iPhone or Android captures stunning 4K iris fibers in 10 seconds with these 3 rules.
        </p>

        {/* Tab Switcher */}
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setActiveTab('human')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'human'
                ? 'bg-[#f5c542] text-black shadow-lg shadow-[#f5c542]/20'
                : 'bg-white/5 text-zinc-400 hover:text-white'
            }`}
          >
            👤 Human Eyes
          </button>
          <button
            onClick={() => setActiveTab('pet')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'pet'
                ? 'bg-[#f5c542] text-black shadow-lg shadow-[#f5c542]/20'
                : 'bg-white/5 text-zinc-400 hover:text-white'
            }`}
          >
            🐾 Pet Eyes (Dogs & Cats)
          </button>
          <button
            onClick={() => setActiveTab('veo')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'veo'
                ? 'bg-gradient-to-r from-purple-500 to-indigo-500 text-white shadow-lg'
                : 'bg-white/5 text-zinc-400 hover:text-white'
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Veo 3.1 Video Studio</span>
          </button>
        </div>
      </div>

      {/* Content: Human Guide */}
      {activeTab === 'human' && (
        <div>
          {/* 3 Step Visual Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {/* Step 1 */}
            <div className="bg-[#0c0f18] border border-white/10 p-6 sm:p-7 rounded-2xl relative overflow-hidden group hover:border-[#f5c542]/40 transition-all shadow-xl">
              <div className="w-12 h-12 rounded-xl bg-[#f5c542]/10 border border-[#f5c542]/30 flex items-center justify-center text-[#f5c542] font-black text-xl mb-5">
                1
              </div>
              <h3 className="font-luxury text-lg font-bold text-white mb-2 flex items-center gap-2">
                <span>Side Flashlight (45° Angle)</span>
              </h3>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Turn on your phone's flashlight or hold another phone's light from a 45° angle from the side. This illuminates the deep microscopic 3D ridges without blinding your pupil.
              </p>
              <div className="mt-4 text-[11px] text-[#f5c542] font-medium">
                💡 Pro tip: Do not shine light straight into your pupil.
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-[#0c0f18] border border-white/10 p-6 sm:p-7 rounded-2xl relative overflow-hidden group hover:border-[#f5c542]/40 transition-all shadow-xl">
              <div className="w-12 h-12 rounded-xl bg-[#f5c542]/10 border border-[#f5c542]/30 flex items-center justify-center text-[#f5c542] font-black text-xl mb-5">
                2
              </div>
              <h3 className="font-luxury text-lg font-bold text-white mb-2">
                Hold 10 cm Away & Tap Focus
              </h3>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Hold the phone approximately 10 cm (4 inches) from your eye. Tap the eye on your smartphone screen to lock razor-sharp focus onto the iris crypt fibers.
              </p>
              <div className="mt-4 text-[11px] text-[#f5c542] font-medium">
                🔍 Pro tip: Use the 1x or 2x main back camera for highest optical resolution.
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-[#0c0f18] border border-white/10 p-6 sm:p-7 rounded-2xl relative overflow-hidden group hover:border-[#f5c542]/40 transition-all shadow-xl">
              <div className="w-12 h-12 rounded-xl bg-[#f5c542]/10 border border-[#f5c542]/30 flex items-center justify-center text-[#f5c542] font-black text-xl mb-5">
                3
              </div>
              <h3 className="font-luxury text-lg font-bold text-white mb-2">
                Open Wide & Gaze Ahead
              </h3>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Open your eye wide (gently lift your upper eyelid with two clean fingers if your eyelashes cover the iris) and look straight into the lens. Snap!
              </p>
              <div className="mt-4 text-[11px] text-[#f5c542] font-medium">
                ✨ Pro tip: Take 2-3 shots; our algorithm automatically picks the sharpest.
              </div>
            </div>
          </div>

          {/* Good vs Bad Visual Comparison */}
          <div className="bg-gradient-to-br from-white/[0.04] to-white/[0.01] border border-white/10 rounded-2xl p-6 sm:p-8">
            <h4 className="font-luxury text-base font-bold text-zinc-200 mb-6 text-center uppercase tracking-wider">
              Quick Visual Checklist: Good vs. Bad Photos
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Good Card */}
              <div className="flex items-start gap-4 bg-emerald-950/25 border border-emerald-500/40 p-5 rounded-xl">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                  <Check className="w-5 h-5 stroke-[2.5]" />
                </div>
                <div>
                  <h5 className="text-sm font-bold text-emerald-300 mb-1">PERFECT RESULT (ACCEPTABLE)</h5>
                  <ul className="text-xs text-zinc-300 space-y-1.5">
                    <li>• Sharp, in-focus textured iris fibers</li>
                    <li>• Side illumination reveals golden/amber crypts</li>
                    <li>• Full circle of iris visible without heavy squinting</li>
                  </ul>
                </div>
              </div>

              {/* Bad Card */}
              <div className="flex items-start gap-4 bg-rose-950/25 border border-rose-500/40 p-5 rounded-xl">
                <div className="w-8 h-8 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                  <X className="w-5 h-5 stroke-[2.5]" />
                </div>
                <div>
                  <h5 className="text-sm font-bold text-rose-300 mb-1">WHAT TO AVOID</h5>
                  <ul className="text-xs text-zinc-300 space-y-1.5">
                    <li>• Blurry image from phone shake or moving too fast</li>
                    <li>• Large window directly in front covering entire pupil</li>
                    <li>• Closed eyelids covering more than 40% of iris</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content: Pet Guide */}
      {activeTab === 'pet' && (
        <div className="bg-[#0c0f18] border border-white/10 p-8 rounded-2xl max-w-4xl mx-auto shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🐾</span>
            <div>
              <h3 className="font-luxury text-xl font-bold text-white">
                How to Photograph Your Dog or Cat's Eye
              </h3>
              <p className="text-xs text-zinc-400">
                Animals have uniquely slit or oval pupils and breathtaking marble-like irises.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-zinc-300 mb-6">
            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
              <span className="font-bold text-[#f5c542] block mb-1">1. The Treat Trick</span>
              <p>Hold your pet's favorite treat right above the camera lens. They will look directly at the phone with wide, curious eyes.</p>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
              <span className="font-bold text-[#f5c542] block mb-1">2. Soft Daylight</span>
              <p>Do NOT use harsh direct flash on pets. Position them near an open window during daytime so their eyes naturally expand.</p>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/5">
              <span className="font-bold text-[#f5c542] block mb-1">3. Burst Mode</span>
              <p>Pets move quickly! Hold down the shutter button for Burst Mode (10 shots) and upload the sharpest single frame.</p>
            </div>
          </div>

          <div className="bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-xl text-xs text-emerald-200">
            ✓ <strong>Zero Surcharge for Pets:</strong> You can choose 2, 3, or more eyes in the studio and dedicate any slot to your pet companion.
          </div>
        </div>
      )}

      {/* Content: Veo 3.1 Studio Prompt */}
      {activeTab === 'veo' && (
        <div className="bg-gradient-to-br from-purple-950/40 via-[#0c0f18] to-indigo-950/40 border border-purple-500/30 p-8 rounded-2xl max-w-4xl mx-auto shadow-2xl">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs text-purple-300 font-bold uppercase tracking-wider mb-1">
                <Video className="w-4 h-4 text-purple-400" />
                <span>Google Veo 3.1 / Sora UGC Video Generator</span>
              </div>
              <h3 className="font-luxury text-xl font-bold text-white">
                15-Second Viral UGC Storyboard Prompt
              </h3>
            </div>
            <button
              onClick={copyToClipboard}
              className="bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-purple-600/30"
            >
              {copiedPrompt ? <CheckCheck className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
              <span>{copiedPrompt ? 'Copied to Clipboard!' : 'Copy Veo 3.1 Prompt'}</span>
            </button>
          </div>

          <p className="text-xs text-zinc-300 mb-4 leading-relaxed">
            Directly modeled after professional AI video creators. Paste this prompt into Google Veo 3.1, Google Flow, or OpenAI Sora to generate high-converting vertical UGC ads:
          </p>

          <pre className="bg-black/80 border border-white/10 p-5 rounded-xl text-[11px] text-purple-200 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {veoPrompt}
          </pre>
        </div>
      )}
    </section>
  );
};
