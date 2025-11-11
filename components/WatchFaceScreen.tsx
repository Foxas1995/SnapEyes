

import React from 'react';
import { ArrowLeftIcon, DownloadIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';

interface WatchFaceScreenProps {
  imageDataUrl: string | undefined;
  onBack: () => void;
}

const WatchFaceScreen: React.FC<WatchFaceScreenProps> = ({ imageDataUrl, onBack }) => {
  const { t } = useLocalization();

  const handleDownload = () => {
    if (!imageDataUrl) return;
    
    // Create a temporary link to trigger the download
    const link = document.createElement('a');
    link.href = imageDataUrl;
    // Use a specific name so users can find it easily
    link.download = `snapeyes_watchface_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!imageDataUrl) {
      return (
         <div className="flex flex-col min-h-full bg-black justify-center items-center p-8 text-center">
             <p className="text-red-400 mb-4">{t('noImageToPreview')}</p>
             <button 
                onClick={onBack} 
                className="px-6 py-3 bg-gray-800 text-white rounded-full hover:bg-gray-700"
             >
                 {t('goBack')}
             </button>
         </div>
      )
  }

  return (
    <div className="flex flex-col min-h-full bg-black animate-fade-in">
       <style>{`
        .animate-fade-in {
          animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
      
      {/* Header */}
      <header className="p-4 flex items-center relative z-10">
        <button 
            onClick={onBack} 
            className="p-2 rounded-full bg-gray-900/50 text-white hover:bg-gray-800 transition-colors absolute left-4" 
            aria-label={t('goBack')}
        >
          <ArrowLeftIcon className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-bold text-white w-full text-center">{t('watchFaceTitle')}</h1>
      </header>

      <main className="flex-grow flex flex-col items-center justify-start pt-6 pb-6 px-6 overflow-y-auto scrollbar-hide">
        {/* Smartwatch Preview Mockup */}
        <div className="flex flex-col items-center flex-shrink-0">
            <div className="relative w-[260px] h-[324px] sm:w-[300px] sm:h-[374px] bg-black rounded-[3rem] ring-[12px] ring-gray-800 shadow-2xl overflow-hidden flex items-center justify-center mb-8 transition-all ease-in-out duration-300">
                
                {/* Realistic Screen Glare Overlay */}
                <div className="absolute inset-0 bg-gradient-to-tr from-white/10 via-transparent to-transparent pointer-events-none z-30 rounded-[3rem]"></div>
                
                {/* The Iris Image */}
                <img 
                    src={imageDataUrl} 
                    alt="Watch Face Preview" 
                    className="absolute inset-0 w-full h-full object-cover z-10"
                />
                
                {/* Time Overlay for Context */}
                <div className="absolute top-8 right-0 left-0 flex flex-col items-center z-20 mix-blend-screen opacity-90 pointer-events-none">
                    <span className="text-white text-6xl sm:text-7xl font-medium tracking-tighter leading-none drop-shadow-lg">10:09</span>
                    <span className="text-cyan-300 text-sm sm:text-base uppercase tracking-widest mt-2 font-semibold drop-shadow-md">WED 24</span>
                </div>
                
                 {/* Mockup Complications */}
                <div className="absolute bottom-6 left-7 w-10 h-10 bg-black/40 backdrop-blur-md rounded-full flex items-center justify-center z-20 border border-white/10">
                     <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                </div>
                 <div className="absolute bottom-6 right-7 w-10 h-10 bg-black/40 backdrop-blur-md rounded-full flex items-center justify-center z-20 border border-white/10 text-xs text-cyan-400 font-bold">
                     72°
                </div>
            </div>
        </div>
        
        <div className="max-w-xs text-center space-y-3 flex-shrink-0">
            <h3 className="text-white font-bold text-xl">{t('watchFaceLooksStunning')}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
                {t('watchFaceInstructions')}
            </p>
        </div>
      </main>

      <footer className="p-6 bg-gray-900/80 backdrop-blur-xl border-t border-white/5 flex-shrink-0">
        <button
            onClick={handleDownload}
            className="w-full bg-cyan-500 hover:bg-cyan-400 text-black font-bold py-4 px-6 rounded-full flex items-center justify-center space-x-3 transition-all duration-200 ease-in-out transform active:scale-95 shadow-lg shadow-cyan-500/20"
        >
            <DownloadIcon className="w-6 h-6" />
            <span>{t('saveImageToPhotos')}</span>
        </button>
      </footer>
    </div>
  );
};

export default WatchFaceScreen;