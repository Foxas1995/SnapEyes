import React, { useState, useCallback, useMemo } from 'react';
import { applyEffectToEyeImage } from '../services/geminiService';
import { ArrowLeftIcon, SparklesIcon, UndoIcon, RedoIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';
import { translations } from '../lib/translations';

interface EditScreenProps {
  baseImage: string;
  onExport: (editedImageDataUrl: string) => void;
  onBack: () => void;
}

type EffectKey = keyof typeof translations.en & ('cosmic' | 'luminous' | 'celestial' | 'liquid' | 'ethereal' | 'aura' | 'shatter' | 'inferno');

interface HistoryState {
  image: string;
  effectKey: EffectKey | null;
}

const effectPrompts: Record<EffectKey, string> = {
  cosmic: "**PROFESSIONAL RETOUCHING TASK:** Apply a subtle 'Cosmic Dust' effect to this iris.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The natural fibrous texture of the iris is paramount. It must not be obscured. The effect is an *addition*, not a replacement.\n\n**EFFECT DETAILS:** Overlay a delicate, sparkling field of cosmic dust around the outer edge of the iris, with a few faint, wispy trails of nebula gas that match the iris's natural colors. The core structure and details of the iris must remain perfectly sharp and clear. The effect should look like the iris is floating in a gentle, beautiful starfield, not exploding. 1:1 aspect ratio.",
  luminous: "**PROFESSIONAL RETOUCHING TASK:** Apply a subtle 'Luminous' glow effect.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** Do not alter or smooth out the natural fiber texture of the iris. The glow should enhance the existing details, not hide them.\n\n**EFFECT DETAILS:** Make the natural fibers of the iris emit a soft, internal light (bioluminescence). The light's color must be a slightly more saturated version of the iris's own pigment. The glow should be strongest in the denser parts of the iris and fainter in others, enhancing the natural 3D texture and depth. The overall effect should be magical but organic, preserving every detail. 1:1 aspect ratio.",
  celestial: "**PROFESSIONAL RETOUCHING TASK:** Frame this iris with a 'Celestial' aura.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The iris itself must remain completely unchanged and realistic. This effect is purely about the background and surrounding aura.\n\n**EFFECT DETAILS:** Keep the iris photo exactly as provided. Around the outer perimeter of the iris, create a soft, ethereal nebula cloud that perfectly matches the colors of the iris. Sprinkle tiny, subtle stars into the black background. The iris should look like a planet viewed from space, with its atmosphere glowing. Do not modify the iris texture or details. 1:1 aspect ratio.",
  liquid: "**PROFESSIONAL RETOUCHING TASK:** Add a 'Liquid Splash' effect around the iris.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The iris itself must remain perfectly intact, sharp, and realistic. The effect must not touch or distort the iris.\n\n**EFFECT DETAILS:** Create a dynamic, high-speed splash of clear liquid surrounding the iris, as if the iris just dropped into water. The liquid should be splashing outwards from behind the iris. The lighting on the splashes should be dramatic, catching highlights. The iris itself should stay pristine and untouched. 1:1 aspect ratio.",
  ethereal: "**PROFESSIONAL RETOUCHING TASK:** Add 'Ethereal Wisps' around the iris.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The detailed, fibrous structure of the iris must be fully preserved. The effect is external to the iris.\n\n**EFFECT DETAILS:** Create delicate, soft wisps of colored smoke or light gently curling around the outer edge of the iris. The color of these wisps must be derived from the natural colors within the iris. The iris itself should remain sharp and untouched, appearing as if it is a magical object emitting this gentle aura. The effect should be subtle and elegant. 1:1 aspect ratio.",
  aura: "**PROFESSIONAL RETOUCHING TASK:** Encircle this iris with a celestial 'Aura'.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The iris itself must remain completely unchanged, sharp, and realistic. The effect is purely external.\n\n**EFFECT DETAILS:** Create a soft, bright, glowing ring of light that tightly frames the outer edge of the iris, similar to a solar eclipse's corona. The color of the glow should be a pale, ethereal blue or white. The background should be filled with a dense, beautiful field of distant stars. The iris must not be altered. 1:1 aspect ratio.",
  shatter: "**PROFESSIONAL RETOUCHING TASK:** Apply a dynamic 'Shatter' effect to this iris.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** While the edges will be altered, the core, central structure of the iris must remain recognizable and detailed.\n\n**EFFECT DETAILS:** Make the outer edges of the iris appear to be exploding or dissolving into a fine spray of sharp, crystalline particles. These particles should trail off into the black background. Enhance the internal fibers of the iris to look slightly more electric and fractured, as if it's breaking apart from within. The effect should be energetic and dynamic. 1:1 aspect ratio.",
  inferno: "**PROFESSIONAL RETOUCHING TASK:** Transform this iris with a fiery 'Inferno' effect.\n\n**MANDATORY GLOBAL CONSTRAINT:** The final image MUST have a PURE BLACK (#000000) background.\n\n**PRIMARY GOAL: PRESERVE STRUCTURE.** The fundamental fiber pattern of the iris should be the basis for the effect, not completely replaced.\n\n**EFFECT DETAILS:** Make the iris glow from within like cooling lava. The natural fibers and crypts should be traced with lines of fiery orange and yellow light, as if they are cracks in volcanic rock. Add a soft, warm, glowing aura around the entire iris that casts a subtle light. The effect should be intense and powerful, like looking into the heart of a volcano. 1:1 aspect ratio.",
};

const effectKeys = Object.keys(effectPrompts) as EffectKey[];

const EditScreen: React.FC<EditScreenProps> = ({
  baseImage,
  onExport,
  onBack,
}) => {
  const { t } = useLocalization();
  const [showOriginal, setShowOriginal] = useState(false);
  const [history, setHistory] = useState<HistoryState[]>([{ image: baseImage, effectKey: null }]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [isApplyingEffect, setIsApplyingEffect] = useState<boolean>(false);
  const [applyingEffectKey, setApplyingEffectKey] = useState<EffectKey | null>(null);

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;
  const currentHistoryState = history[historyIndex];
  const selectedEffect = currentHistoryState.effectKey;
  
  const handleApplyEffect = useCallback(async (effectKey: EffectKey) => {
    if (isApplyingEffect) return;
    
    setApplyingEffectKey(effectKey);
    setIsApplyingEffect(true);

    try {
      const base64Data = baseImage.split(',')[1];
      const resultBase64 = await applyEffectToEyeImage(base64Data, effectPrompts[effectKey]);
      
      const newImage = `data:image/png;base64,${resultBase64}`;
      const newHistoryState: HistoryState = { image: newImage, effectKey };
      
      const newHistory = history.slice(0, historyIndex + 1);
      newHistory.push(newHistoryState);
      
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);

    } catch (error) {
      console.error("Failed to apply effect:", error);
      alert("Sorry, we couldn't apply this effect. Please try again.");
    } finally {
      setIsApplyingEffect(false);
      setApplyingEffectKey(null);
    }
  }, [baseImage, isApplyingEffect, history, historyIndex]);
  
  const handleExportClick = () => {
    onExport(currentHistoryState.image);
  };
  
  const handleUndo = useCallback(() => {
    if (canUndo) {
      setHistoryIndex(prev => prev - 1);
    }
  }, [canUndo]);

  const handleRedo = useCallback(() => {
    if (canRedo) {
      setHistoryIndex(prev => prev + 1);
    }
  }, [canRedo]);
  
  const currentImage = useMemo(() => {
    return showOriginal ? history[0].image : currentHistoryState.image;
  }, [showOriginal, history, currentHistoryState]);

  const EffectButton: React.FC<{
    effectKey: EffectKey;
  }> = ({ effectKey }) => (
    <button
      onClick={() => handleApplyEffect(effectKey)}
      disabled={isApplyingEffect}
      className={`px-3 py-3 rounded-full font-semibold text-sm transition-colors text-center
        ${selectedEffect === effectKey ? 'bg-cyan-500 text-black' : 'bg-gray-700 text-white'}
        ${isApplyingEffect ? 'opacity-50 cursor-not-allowed' : 'hover:bg-cyan-600 active:bg-cyan-700'}
      `}
    >
      {t(effectKey)}
    </button>
  );

  return (
    <div className="min-h-full w-full flex flex-col bg-black">
      <header className="p-4 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <button onClick={onBack} className="p-2 rounded-full hover:bg-gray-800" aria-label={t('goBack')}>
            <ArrowLeftIcon className="w-6 h-6" />
          </button>
          <button onClick={handleUndo} disabled={!canUndo} className="p-2 rounded-full hover:bg-gray-800 disabled:text-gray-600 disabled:hover:bg-transparent disabled:cursor-not-allowed" aria-label={t('undo')}>
              <UndoIcon className="w-6 h-6" />
          </button>
          <button onClick={handleRedo} disabled={!canRedo} className="p-2 rounded-full hover:bg-gray-800 disabled:text-gray-600 disabled:hover:bg-transparent disabled:cursor-not-allowed" aria-label={t('redo')}>
              <RedoIcon className="w-6 h-6" />
          </button>
        </div>
        
        <button
          onMouseDown={() => setShowOriginal(true)}
          onMouseUp={() => setShowOriginal(false)}
          onTouchStart={() => setShowOriginal(true)}
          onTouchEnd={() => setShowOriginal(false)}
          className="px-4 py-2 text-sm border border-gray-600 rounded-full hover:bg-gray-800 select-none"
        >
          {showOriginal ? t('baseImage') : t('holdToCompare')}
        </button>
      </header>

      <main className="flex-grow flex items-center justify-center p-4 relative">
        <div className="relative max-w-full max-h-full">
            <img
              src={currentImage}
              alt="Enhanced Eye"
              className="block max-w-full max-h-full object-contain rounded-lg"
              style={{aspectRatio: '1 / 1'}}
            />
            {isApplyingEffect && (
                <div 
                    className="absolute inset-0 rounded-lg ring-2 ring-cyan-500 animate-pulse pointer-events-none"
                    role="status"
                >
                    {applyingEffectKey && <span className="sr-only">{t('applyingEffect')} {t(applyingEffectKey)}...</span>}
                </div>
            )}
        </div>
      </main>
      
      <footer className="p-4 bg-gray-900/80 backdrop-blur-sm">
        <div className="mb-4">
            <h3 className="text-center text-lg font-semibold text-white mb-3" id="effects-list-label">{t('aiEffects')}</h3>
            <div className="grid grid-cols-3 gap-2" role="group" aria-labelledby="effects-list-label">
              {effectKeys.map((key) => (
                <EffectButton key={key} effectKey={key} />
              ))}
            </div>
        </div>

        <button
          onClick={handleExportClick}
          disabled={historyIndex === 0 || isApplyingEffect}
          className="w-full mt-2 bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-4 rounded-full flex items-center justify-center space-x-2 transition-transform duration-200 ease-in-out transform hover:scale-105 disabled:bg-gray-600 disabled:scale-100 disabled:cursor-not-allowed"
        >
          <SparklesIcon className="w-5 h-5" />
          <span>{t('export')}</span>
        </button>
      </footer>
    </div>
  );
};

export default EditScreen;
