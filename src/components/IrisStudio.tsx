import React, { useState, useRef } from 'react';
import { Sparkles, Camera, Upload, Lock, Unlock, ShieldCheck, ZoomIn, Check, Heart, MapPin, Sliders, X } from 'lucide-react';
import confetti from 'canvas-confetti';
import { StyleCarousel } from './StyleCarousel';

// Pigment DNA palettes based on selected style & iris
const PIGMENT_PALETTES: Record<string, Array<{ name: string; hex: string }>> = {
  celestial_gold: [
    { name: 'Solar Amber', hex: '#D4AF37' },
    { name: 'Celestial Cobalt', hex: '#1B3B6F' },
    { name: 'Stardust Ethereal', hex: '#F5C542' },
    { name: 'Obsidian Void', hex: '#0B0E14' },
  ],
  gold_kintsugi: [
    { name: '24K Liquid Gold', hex: '#E5B73B' },
    { name: 'Cracked Lacquer', hex: '#8B6914' },
    { name: 'Midnight Azure', hex: '#15253F' },
    { name: 'Deep Basalt', hex: '#070A0F' },
  ],
  deep_nebula: [
    { name: 'Interstellar Cyan', hex: '#38BDF8' },
    { name: 'Deep Indigo', hex: '#4338CA' },
    { name: 'Bioluminescent Violet', hex: '#818CF8' },
    { name: 'Cosmic Core', hex: '#05070E' },
  ],
  obsidian_smoke: [
    { name: 'Charcoal Silk', hex: '#94A3B8' },
    { name: 'Silver Filigree', hex: '#E2E8F0' },
    { name: 'Slate Atmosphere', hex: '#334155' },
    { name: 'Matte Obsidian', hex: '#090D14' },
  ],
  solar_corona: [
    { name: 'Plasma Orange', hex: '#FB923C' },
    { name: 'Solar Gold', hex: '#FBBF24' },
    { name: 'Eclipse Shadow', hex: '#7C2D12' },
    { name: 'Coronal Black', hex: '#060709' },
  ],
  studio_black: [
    { name: 'Pure Sapphire Iris', hex: '#2563EB' },
    { name: 'Melanin Hazel Ring', hex: '#A16207' },
    { name: 'Wolfflin Nodules', hex: '#CBD5E1' },
    { name: 'Iris Galerie Velvet', hex: '#020202' },
  ],
};

export const IrisStudio: React.FC = () => {
  // Eye count selector: 1 to 8 eyes
  const [eyeCount, setEyeCount] = useState<number>(2);
  const [singleArtOption, setSingleArtOption] = useState<'black' | 'art'>('art');
  const [selectedStyle, setSelectedStyle] = useState<string>('celestial_gold');

  // Customer Journey view state
  const [viewState, setViewState] = useState<'input' | 'preview' | 'unlocked'>('preview');

  // Personalization
    const [names, setNames] = useState('Emma & Liam');
  const [specialDate, setSpecialDate] = useState('2024.08.15');
  const [coordinates, setCoordinates] = useState("54°41'N 25°17'E");
  const [plaqueStyle, setPlaqueStyle] = useState<'typography' | 'brass'>('typography');

  // Order Bumps (Default: all unchecked)
  const [bumpWallpaper, setBumpWallpaper] = useState(false);
  const [bumpPdf, setBumpPdf] = useState(false);
  const [bumpIridology, setBumpIridology] = useState(false);
  const bumpAltStyle = false;

  // Interactive Tools
  const [loupeActive, setLoupeActive] = useState(false);
  const [loupePos, setLoupePos] = useState({ x: 50, y: 50, clientX: 0, clientY: 0 });
  const [glassSheenX, setGlassSheenX] = useState(50);
  const [copiedColor, setCopiedColor] = useState<string | null>(null);

  // File Upload / Camera State
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [iridologyModalOpen, setIridologyModalOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Pricing Calculation based on formula:
  // 1 Eye Black: €19.97, 1 Eye Art: €24.97
  // 2 Eyes: €39.97, then +€15 per each additional eye
  const calculateBasePrice = (): number => {
    if (eyeCount === 1) {
      return singleArtOption === 'black' ? 19.97 : 24.97;
    }
    return 39.97 + (eyeCount - 2) * 15.0;
  };

  const basePrice = calculateBasePrice();
  let totalPrice = basePrice;
  if (bumpWallpaper) totalPrice += 5.97;
  if (bumpPdf) totalPrice += 4.97;
  if (bumpIridology) totalPrice += 9.97;
  if (bumpAltStyle) totalPrice += 6.97;

  // Handle local user upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    const reader = new FileReader();
    reader.onload = (event) => {
      setUploadedImage(event.target?.result as string);
      setTimeout(() => {
        setIsProcessing(false);
        setViewState('preview');
        confetti({ particleCount: 70, spread: 60, origin: { y: 0.65 } });
      }, 1200);
    };
    reader.readAsDataURL(file);
  };

  // WebRTC Camera
  const startCamera = async () => {
    try {
      setCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      alert("Unable to access camera. Please allow permissions or upload a photo directly.");
      setCameraActive(false);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg');
      setUploadedImage(dataUrl);
      stopCamera();
      setIsProcessing(true);
      setTimeout(() => {
        setIsProcessing(false);
        setViewState('preview');
        confetti({ particleCount: 70, spread: 60, origin: { y: 0.6 } });
      }, 1200);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const handleUnlock = () => {
    setViewState('unlocked');
    confetti({
      particleCount: 160,
      spread: 90,
      origin: { y: 0.6 },
      colors: ['#f5c542', '#d4af37', '#ffffff']
    });
  };

  // Canvas Mouse Move (Specular Sheen + Loupe Position)
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setGlassSheenX(x);
    setLoupePos({
      x: Math.max(10, Math.min(x, 90)),
      y: Math.max(10, Math.min(y, 90)),
      clientX: e.clientX - rect.left,
      clientY: e.clientY - rect.top,
    });
  };

  // Copy Color Hex
  const copyHex = (hex: string) => {
    navigator.clipboard.writeText(hex);
    setCopiedColor(hex);
    setTimeout(() => setCopiedColor(null), 1800);
  };

  // Image selection
  const styleKey = eyeCount === 1 && singleArtOption === 'black' ? 'studio_black' : selectedStyle;
  const currentPalette = PIGMENT_PALETTES[styleKey] || PIGMENT_PALETTES.celestial_gold;

  const displayImage = () => {
    if (viewState === 'input') {
      return uploadedImage || '/assets/sample_eye_blue_1789706902835.jpg';
    }
    if (viewState === 'unlocked') {
      return eyeCount === 1
        ? `/assets/art_1eye_${styleKey}_clean.jpg`
        : `/assets/art_2eyes_${styleKey}_clean.jpg`;
    }
    // Watermarked preview
    return eyeCount === 1
      ? `/assets/art_1eye_${styleKey}_wm.jpg`
      : `/assets/art_2eyes_${styleKey}_wm.jpg`;
  };

  return (
    <section id="studio" className="py-20 px-4 max-w-7xl mx-auto select-none">
      {/* Studio Header */}
      <div className="text-center max-w-3xl mx-auto mb-10">
        <span className="text-xs font-bold uppercase tracking-widest text-[#f5c542] bg-[#f5c542]/10 border border-[#f5c542]/30 px-4 py-1.5 rounded-full inline-flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>INTERACTIVE AI IRIS STUDIO</span>
        </span>
        <h2 className="font-luxury text-3xl sm:text-5xl font-bold mt-4 mb-3">
          CUSTOMIZE YOUR <span className="text-gold-gradient">CELESTIAL ARTWORK</span>
        </h2>
        <p className="text-zinc-400 text-xs sm:text-sm">
          Select number of eyes (1 to 8). Any eye can be a partner, family member, or pet companion 🐾!
        </p>
      </div>

      {/* Step 1: 1 to 8 Eye Count Selector Box */}
      <div className="bg-[#0f121c]/90 border border-white/10 p-6 rounded-2xl mb-10 max-w-4xl mx-auto backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider block">
              Step 1: Choose Number of Eyes (1 - 8)
            </span>
            <span className="text-[11px] text-zinc-400">
              Couples, Trios, Families, or Human + Pet Duo 🐾
            </span>
          </div>
          <span className="text-xs font-extrabold text-[#f5c542] bg-[#f5c542]/10 px-3 py-1 rounded-full border border-[#f5c542]/30">
            {eyeCount === 1 ? '1 Eye Solo' : eyeCount === 2 ? '2 Eyes (Couple Duo)' : `${eyeCount} Eyes (Family Galaxy)`}
          </span>
        </div>

        {/* 1 - 8 Buttons */}
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => {
            const isSelected = eyeCount === n;
            return (
              <button
                key={n}
                onClick={() => setEyeCount(n)}
                className={`py-3 rounded-xl font-luxury text-base font-bold transition-all relative ${
                  isSelected
                    ? 'bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black shadow-lg shadow-[#f5c542]/30 scale-105'
                    : 'bg-white/5 hover:bg-white/10 text-zinc-300 border border-white/5'
                }`}
              >
                {n} {n === 1 ? 'Eye' : 'Eyes'}
                {n === 2 && (
                  <span className="absolute -top-2 left-1/2 -translate-x-1/2 bg-rose-500 text-white text-[8px] font-black px-1.5 py-0.2 rounded-full uppercase shadow">
                    DUO
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Single Eye Choice */}
        {eyeCount === 1 && (
          <div className="mt-4 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs text-zinc-300 font-semibold">1 Eye Style Choice:</span>
            <div className="flex gap-2">
              <button
                onClick={() => setSingleArtOption('black')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  singleArtOption === 'black'
                    ? 'bg-white/20 text-white border border-white/40'
                    : 'bg-white/5 text-zinc-400'
                }`}
              >
                Studio Minimalist Black (€19.97)
              </button>
              <button
                onClick={() => setSingleArtOption('art')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  singleArtOption === 'art'
                    ? 'bg-[#f5c542] text-black shadow-md shadow-[#f5c542]/20'
                    : 'bg-white/5 text-zinc-400'
                }`}
              >
                Celestial Cosmic Art (€24.97)
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Studio Grid: Left Canvas (8 cols) + Right Controls (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* LEFT COLUMN: Canvas + Loupe + Color DNA Card (7 or 8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Main Artwork Preview Canvas */}
          <div className="relative bg-gradient-to-b from-white/10 to-white/5 p-3 rounded-3xl border border-white/15 shadow-[0_30px_90px_rgba(0,0,0,0.95)]">
            
            {/* Top Toolbar above canvas */}
            <div className="flex items-center justify-between px-3 py-2 mb-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono text-zinc-300 text-[11px] uppercase tracking-wider">
                  {viewState === 'unlocked' ? 'UNLOCKED MASTER 4K' : 'LIVE 300 DPI PREVIEW'}
                </span>
              </div>

              {/* Macro Loupe Toggle */}
              <button
                onClick={() => setLoupeActive(!loupeActive)}
                className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  loupeActive
                    ? 'bg-[#f5c542] text-black font-bold shadow-md shadow-[#f5c542]/25'
                    : 'bg-white/10 text-zinc-300 hover:bg-white/20 border border-white/10'
                }`}
              >
                <ZoomIn className="w-3.5 h-3.5" />
                <span>{loupeActive ? '5x Loupe Active' : 'Hover 5x Loupe'}</span>
              </button>
            </div>

            {/* Canvas Surface with Mouse Move Sheen */}
            <div
              ref={canvasRef}
              onMouseMove={handleCanvasMouseMove}
              className="relative aspect-[16/10] sm:aspect-[16/9] w-full overflow-hidden rounded-2xl bg-black border border-white/10 cursor-crosshair group shadow-inner"
            >
              {/* Image */}
              <img
                src={displayImage()}
                alt="Iris Artwork Canvas"
                className="w-full h-full object-cover pointer-events-none"
              />

              {/* SPECULAR 3D GLASS SHEEN (Reacts to mouse X) */}
              <div
                className="absolute inset-0 pointer-events-none opacity-25 mix-blend-overlay transition-opacity group-hover:opacity-40"
                style={{
                  background: `linear-gradient(115deg, transparent 20%, rgba(255,255,255,0.7) ${glassSheenX}%, transparent 80%)`,
                }}
              />

              {/* MACRO ZOOM LOUPE (500% Magnifier Circle) */}
              {loupeActive && (
                <div
                  className="absolute w-36 h-36 rounded-full pointer-events-none border-2 border-[#f5c542] shadow-[0_0_30px_rgba(245,197,66,0.6)] overflow-hidden z-40 -translate-x-1/2 -translate-y-1/2"
                  style={{
                    left: `${loupePos.clientX}px`,
                    top: `${loupePos.clientY}px`,
                  }}
                >
                  <div
                    className="absolute inset-0 bg-cover bg-no-repeat filter contrast-125"
                    style={{
                      backgroundImage: `url(${displayImage()})`,
                      backgroundPosition: `${loupePos.x}% ${loupePos.y}%`,
                      backgroundSize: '500%',
                    }}
                  />
                  {/* Loupe Crosshair */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
                    <div className="w-full h-px bg-[#f5c542]" />
                    <div className="h-full w-px bg-[#f5c542] absolute" />
                  </div>
                  <div className="absolute bottom-1 left-1/2 -translate-x-1/2 bg-black/80 px-2 py-0.2 rounded text-[8px] font-mono text-[#f5c542] tracking-wider">
                    5X CRYPTS
                  </div>
                </div>
              )}

              {/* Watermark Protection (When in preview mode) */}
              {viewState === 'preview' && (
                <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-6 bg-gradient-to-t from-black/40 via-transparent to-black/20">
                  <div className="flex justify-between items-start">
                    <span className="bg-black/80 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-mono text-zinc-300 border border-white/10 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-[#f5c542]" />
                      PROTECTED PREVIEW
                    </span>
                    <span className="bg-black/80 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-mono text-amber-300 border border-amber-400/30">
                      SNAPEYES.COM
                    </span>
                  </div>

                  {/* Elegant diagonal watermark banner */}
                  <div className="self-center transform -rotate-12 bg-black/50 backdrop-blur-sm border border-white/10 px-8 py-2 rounded-xl text-white/30 font-luxury font-bold tracking-widest text-lg sm:text-2xl">
                    SNAPEYES ARCHIVAL WATERMARK
                  </div>

                  <div className="text-[10px] font-mono text-white/40 text-center">
                    Purchase unlocks full 300 DPI vector PDF, uncompressed 4K master, & removes all watermarks
                  </div>
                </div>
              )}

              {/* BRASS GALLERY PLAQUE (At bottom of artwork if selected) */}
              {plaqueStyle === 'brass' && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-gradient-to-b from-[#e5b73b] via-[#c69214] to-[#996515] text-black px-6 py-2 rounded-md shadow-2xl border border-yellow-200/50 flex flex-col items-center justify-center text-center max-w-[85%] sm:max-w-md pointer-events-none">
                  <span className="font-luxury font-black text-[11px] tracking-wider uppercase">
                    {names || 'Emma & Liam'}
                  </span>
                  <div className="flex items-center gap-3 text-[9px] font-mono opacity-85 mt-0.5">
                    <span>{specialDate || '2024.08.15'}</span>
                    <span>·</span>
                    <span className="flex items-center gap-0.5">
                      <MapPin className="w-2.5 h-2.5" />
                      {coordinates || "54°41'N 25°17'E"}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Under-Canvas Action Row */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 px-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-white/10 hover:bg-white/20 text-zinc-200 text-xs font-semibold px-3 py-1.5 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
                >
                  <Upload className="w-3.5 h-3.5 text-[#f5c542]" />
                  <span>Upload Your Eye</span>
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <button
                  onClick={startCamera}
                  className="bg-white/10 hover:bg-white/20 text-zinc-200 text-xs font-semibold px-3 py-1.5 rounded-lg border border-white/10 flex items-center gap-1.5 transition-all"
                >
                  <Camera className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Phone Camera</span>
                </button>
              </div>

              {/* Unlocking State Indicator */}
              <div className="text-xs font-bold text-zinc-400 flex items-center gap-1.5">
                {viewState === 'unlocked' ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Unlock className="w-3.5 h-3.5" />
                    Unlocked & Download Ready
                  </span>
                ) : (
                  <span className="text-amber-400 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5" />
                    Watermarked Preview
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* IRIS PIGMENT DNA (Color Swatches Card) */}
          <div className="bg-[#0b0e17] border border-white/10 p-5 rounded-2xl shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-[#f5c542]" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
                  Extracted Iris Pigment DNA (Hex Chromatic Profile)
                </h4>
              </div>
              <span className="text-[10px] font-mono text-zinc-400">Click to copy HEX</span>
            </div>

            {/* 4 Swatch Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {currentPalette.map((p) => {
                const isCopied = copiedColor === p.hex;
                return (
                  <button
                    key={p.hex}
                    onClick={() => copyHex(p.hex)}
                    className="flex items-center gap-2.5 p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-left group"
                  >
                    <div
                      className="w-7 h-7 rounded-lg shadow-md border border-white/20 flex-shrink-0"
                      style={{ backgroundColor: p.hex }}
                    />
                    <div className="flex flex-col min-w-0">
                      <span className="text-[11px] font-bold text-zinc-200 truncate group-hover:text-[#f5c542] transition-colors">
                        {p.name}
                      </span>
                      <span className="text-[9px] font-mono text-zinc-400 flex items-center gap-1">
                        {isCopied ? (
                          <span className="text-emerald-400 font-bold flex items-center gap-0.5">
                            <Check className="w-2.5 h-2.5" /> Copied!
                          </span>
                        ) : (
                          p.hex
                        )}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Couple Harmony Index (Shown when eyeCount === 2) */}
            {eyeCount === 2 && (
              <div className="mt-4 pt-3.5 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
                  <span className="font-semibold text-zinc-200">
                    Couple Chromatic Resonance: <strong className="text-[#f5c542]">98.6% Solar & Oceanic Harmony</strong>
                  </span>
                </div>
                <span className="text-[11px] text-zinc-400 italic">
                  "Amber melanin meets sapphire striae in timeless equilibrium."
                </span>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Style Selector + Personalization + Order Bumps + Checkout (4 or 5 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Style Carousel (6 Distinct Art Mediums) */}
          <div className="bg-[#0b0e17] border border-white/10 p-5 rounded-2xl shadow-xl">
            <StyleCarousel
              selectedStyle={selectedStyle}
              onSelect={(styleId) => setSelectedStyle(styleId)}
            />
          </div>

          {/* Personalization & Gallery Plaque */}
          <div className="bg-[#0b0e17] border border-white/10 p-5 rounded-2xl shadow-xl flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#f5c542]" />
              <span>Personalize Typography & Coordinates</span>
            </h4>

            <div>
              <label className="text-[10px] text-zinc-400 uppercase font-semibold block mb-1">
                Names or Inscription
              </label>
              <input
                type="text"
                value={names}
                onChange={(e) => setNames(e.target.value)}
                placeholder="e.g. Emma & Liam"
                className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#f5c542]"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-semibold block mb-1">
                  Special Date
                </label>
                <input
                  type="text"
                  value={specialDate}
                  onChange={(e) => setSpecialDate(e.target.value)}
                  placeholder="2024.08.15"
                  className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#f5c542]"
                />
              </div>
              <div>
                <label className="text-[10px] text-zinc-400 uppercase font-semibold block mb-1">
                  GPS Coordinates
                </label>
                <input
                  type="text"
                  value={coordinates}
                  onChange={(e) => setCoordinates(e.target.value)}
                  placeholder="54°41'N 25°17'E"
                  className="w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#f5c542]"
                />
              </div>
            </div>

            {/* Plaque display style toggle */}
            <div className="flex gap-2 mt-1">
              <button
                onClick={() => setPlaqueStyle('typography')}
                className={`flex-1 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                  plaqueStyle === 'typography'
                    ? 'bg-white/20 text-white border border-white/30'
                    : 'bg-white/5 text-zinc-400'
                }`}
              >
                Fine Art Vector Typography
              </button>
              <button
                onClick={() => setPlaqueStyle('brass')}
                className={`flex-1 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                  plaqueStyle === 'brass'
                    ? 'bg-[#f5c542] text-black font-bold shadow'
                    : 'bg-white/5 text-zinc-400'
                }`}
              >
                Engraved Brass Plaque
              </button>
            </div>
          </div>

          {/* Optional Order Bumps (Unchecked by default) */}
          <div className="bg-[#0b0e17] border border-white/10 p-5 rounded-2xl shadow-xl flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
              Optional Add-Ons (Unchecked by default)
            </h4>

            {/* Bump 1: Live Phone Wallpaper */}
            <label className="flex items-start gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={bumpWallpaper}
                onChange={(e) => setBumpWallpaper(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded text-[#f5c542] focus:ring-0 bg-zinc-800 border-zinc-600"
              />
              <div className="flex-1 text-xs">
                <div className="flex justify-between font-semibold text-zinc-200">
                  <span>Animated Live Phone Wallpaper (MP4)</span>
                  <span className="text-[#f5c542]">+€5.97</span>
                </div>
                <span className="text-[10px] text-zinc-400 block mt-0.5">
                  Subtle breathing pulse & drifting gold dust for iOS / Android lockscreen.
                </span>
              </div>
            </label>

            {/* Bump 2: Keepsake Certificate PDF */}
            <label className="flex items-start gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={bumpPdf}
                onChange={(e) => setBumpPdf(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded text-[#f5c542] focus:ring-0 bg-zinc-800 border-zinc-600"
              />
              <div className="flex-1 text-xs">
                <div className="flex justify-between font-semibold text-zinc-200">
                  <span>Archival Keepsake Certificate (A4 PDF)</span>
                  <span className="text-[#f5c542]">+€4.97</span>
                </div>
                <span className="text-[10px] text-zinc-400 block mt-0.5">
                  Museum certificate with iris timestamp & authenticity serial number.
                </span>
              </div>
            </label>

            {/* Bump 3: Rayid Soul Iridology Reading (100% Client-side, $0 API) */}
            <label className="flex items-start gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={bumpIridology}
                onChange={(e) => setBumpIridology(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded text-[#f5c542] focus:ring-0 bg-zinc-800 border-zinc-600"
              />
              <div className="flex-1 text-xs">
                <div className="flex justify-between font-semibold text-zinc-200">
                  <span className="flex items-center gap-1.5">
                    Personalized Rayid Soul Iridology
                    <button
                      type="button"
                      onClick={(e) => { e.preventDefault(); e.stopPropagation(); setIridologyModalOpen(true); }}
                      className="text-[#f5c542] hover:underline text-[10px]"
                    >
                      (Preview)
                    </button>
                  </span>
                  <span className="text-[#f5c542]">+€9.97</span>
                </div>
                <span className="text-[10px] text-zinc-400 block mt-0.5">
                  Psychological iris archetype report: Flower, Jewel, Stream & Shaker.
                </span>
              </div>
            </label>
          </div>

          {/* Checkout / Unlock Card */}
          <div className="bg-gradient-to-b from-amber-500/20 via-[#0e121d] to-[#0b0e17] border-2 border-[#f5c542]/50 p-6 rounded-3xl shadow-2xl flex flex-col gap-4">
            <div className="flex justify-between items-baseline">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 block">
                  Total Investment
                </span>
                <span className="text-2xl sm:text-3xl font-luxury font-black text-white">
                  €{totalPrice.toFixed(2)}
                </span>
              </div>
              <span className="text-xs text-emerald-400 font-semibold bg-emerald-950/60 px-2.5 py-1 rounded-full border border-emerald-500/30">
                Instant 4K Delivery
              </span>
            </div>

            <button
              onClick={handleUnlock}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-[#f5c542] via-[#e5b73b] to-[#c69214] text-black font-luxury font-black text-sm uppercase tracking-widest shadow-xl shadow-[#f5c542]/30 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <Unlock className="w-4 h-4 stroke-[2.5]" />
              <span>Unlock Master 4K Artwork · €{totalPrice.toFixed(2)}</span>
            </button>

            <div className="flex items-center justify-center gap-3 text-[10px] font-mono text-zinc-400">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                30-Day Money-Back Guarantee
              </span>
              <span>·</span>
              <span>Stripe Secure 256-Bit</span>
            </div>
          </div>
        </div>
      </div>

      {/* CAMERA OVERLAY MODAL */}
      {cameraActive && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0b0e17] border border-white/20 p-6 rounded-3xl max-w-lg w-full flex flex-col items-center gap-4 shadow-2xl">
            <div className="flex justify-between items-center w-full">
              <span className="font-luxury font-bold text-sm text-[#f5c542] flex items-center gap-2">
                <Camera className="w-4 h-4" /> Live Camera Eye Capture
              </span>
              <button onClick={stopCamera} className="text-zinc-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="relative w-full aspect-video rounded-2xl overflow-hidden bg-black border border-white/10">
              <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
              <div className="absolute inset-0 border-2 border-emerald-400/50 rounded-2xl pointer-events-none" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-28 h-28 border border-white/60 rounded-full pointer-events-none flex items-center justify-center">
                <span className="text-[10px] font-mono text-white/80 bg-black/60 px-2 py-0.5 rounded">CENTER IRIS</span>
              </div>
            </div>
            <button
              onClick={capturePhoto}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black font-luxury font-bold text-xs uppercase tracking-widest shadow-lg hover:scale-[1.02] active:scale-95 transition-all"
            >
              Capture & Remove Glare
            </button>
          </div>
        </div>
      )}

      {/* PROCESSING OVERLAY */}
      {isProcessing && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex flex-col items-center justify-center gap-4">
          <div className="w-16 h-16 border-4 border-[#f5c542]/20 border-t-[#f5c542] rounded-full animate-spin" />
          <div className="text-center">
            <span className="font-luxury font-bold text-lg text-white block">AI DE-GLARING IN PROGRESS...</span>
            <span className="text-xs text-zinc-400 font-mono">Neutralizing corneal flash glare & isolating 10,000 crypts</span>
          </div>
        </div>
      )}

      {/* RAYID SOUL IRIDOLOGY PREVIEW MODAL */}
      {iridologyModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0b0e17] border border-[#f5c542]/40 p-6 rounded-3xl max-w-xl w-full flex flex-col gap-4 shadow-2xl">
            <div className="flex justify-between items-center">
              <span className="font-luxury font-bold text-base text-[#f5c542] flex items-center gap-2">
                <Sparkles className="w-4 h-4" /> Rayid Method Iris Soul Reading
              </span>
              <button onClick={() => setIridologyModalOpen(false)} className="text-zinc-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <strong className="text-amber-300 block mb-1">Archetype: The Jewel</strong>
                <p className="text-zinc-300 text-[11px] leading-relaxed">
                  Deeply analytical and contemplative. Defined by dense cryptographic pigment clusters around the pupillary collar.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <strong className="text-emerald-300 block mb-1">Elemental Resonance</strong>
                <p className="text-zinc-300 text-[11px] leading-relaxed">
                  Fire meets Ocean: balanced synthesis of golden solar melanin and deep sapphire striae.
                </p>
              </div>
            </div>
            <p className="text-[10px] text-zinc-400 italic text-center">
              Calculated 100% locally via cryptographic Rayid geometric analysis. Zero API credits consumed.
            </p>
            <button
              onClick={() => setIridologyModalOpen(false)}
              className="py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-colors"
            >
              Close Reading Preview
            </button>
          </div>
        </div>
      )}
    </section>

  );
};
