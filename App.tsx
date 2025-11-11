
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { AppScreen, HistoryItem, CropData } from './types';
import OnboardingScreen from './components/OnboardingScreen';
import CaptureScreen from './components/CaptureScreen';
import ProcessingScreen from './components/ProcessingScreen';
import EditScreen from './components/EditScreen';
import ExportScreen from './components/ExportScreen';
import StoreScreen from './components/StoreScreen';
import GalleryScreen from './components/GalleryScreen';
import SettingsScreen from './components/SettingsScreen';
import WatchFaceScreen from './components/WatchFaceScreen';
import IridologyScreen from './components/IridologyScreen';
import BottomNav from './components/common/BottomNav';
import Header from './components/common/Header';
import SplashScreen from './components/SplashScreen';
import { useLocalization } from './lib/localization';
import { ComparisonSlider } from './components/common/Slider';
import CropScreen from './components/CropScreen';

const EnhanceResultScreen: React.FC<{
  beforeImage: string;
  afterImage: string;
  onContinue: () => void;
  onRetake: () => void;
}> = ({ beforeImage, afterImage, onContinue, onRetake }) => {
  const { t } = useLocalization();

  return (
    <div className="flex flex-col min-h-full p-6 bg-gray-900 text-center relative animate-in fade-in duration-500">
       <style>{`
        .animate-in { animation-duration: 500ms; }
        .fade-in { animation-name: fadeIn; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
      <h2 className="text-3xl font-bold mb-2">{t('enhancementComplete')}</h2>
      <p className="text-gray-400 mb-6">{t('dragToCompare')}</p>
      
      <div className="flex-grow flex flex-col items-center justify-center mb-6">
        <div className="w-full max-w-xs aspect-square relative rounded-lg overflow-hidden shadow-2xl shadow-cyan-500/20">
            <ComparisonSlider before={beforeImage} after={afterImage} animate={true} />
        </div>
      </div>
      
      <div className="w-full max-w-sm mx-auto grid grid-cols-2 gap-4">
        <button
          onClick={onRetake}
          className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-full transition-colors"
        >
          {t('retake')}
        </button>
        <button
          onClick={onContinue}
          className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-4 rounded-full transition-colors"
        >
          {t('continueToEdit')}
        </button>
      </div>
    </div>
  );
};


const App: React.FC = () => {
  const [screen, setScreen] = useState<AppScreen>(AppScreen.ONBOARDING);
  const [activeTab, setActiveTab] = useState<AppScreen>(AppScreen.CAPTURE);
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [croppedImage, setCroppedImage] = useState<string | null>(null); // This is the "before" image for the slider
  const [enhancedImage, setEnhancedImage] = useState<string | null>(null);
  const [cropData, setCropData] = useState<CropData | null>(null);
  const [credits, setCredits] = useState<number>(3);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [postCaptureDestination, setPostCaptureDestination] = useState<AppScreen | null>(null);
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 2500); // Animation duration
    return () => clearTimeout(timer);
  }, []);


  const goToCapture = useCallback(() => {
    setOriginalImage(null);
    setCroppedImage(null);
    setEnhancedImage(null);
    setCropData(null);
    setScreen(AppScreen.CAPTURE);
    setActiveTab(AppScreen.CAPTURE);
  }, []);

  const resetToHome = useCallback(() => {
    goToCapture();
  }, [goToCapture]);

  const goToEdit = useCallback(() => {
    setScreen(AppScreen.EDIT);
  }, []);

  const goToWatchFace = useCallback(() => {
    setScreen(AppScreen.WATCHFACE);
  }, []);
  
  const goToIridology = useCallback(() => {
    setScreen(AppScreen.IRIDOLOGY);
    setActiveTab(AppScreen.IRIDOLOGY);
  }, []);

  const goToExport = useCallback(() => {
      setScreen(AppScreen.EXPORT);
  }, []);

  const startIridologyCaptureFlow = useCallback(() => {
    setPostCaptureDestination(AppScreen.IRIDOLOGY);
    goToCapture();
  }, [goToCapture]);

  const handleImageCaptured = useCallback((imageDataUrl: string) => {
    setOriginalImage(imageDataUrl);
    setCroppedImage(null);
    setEnhancedImage(null);
    setCropData(null);
    setScreen(AppScreen.CROP);
  }, []);

  const handleCropComplete = useCallback((data: CropData) => {
    setCropData(data);
    setScreen(AppScreen.PROCESSING);
  }, []);

  const handleProcessingComplete = useCallback((composedBeforeDataUrl: string, enhancedImageDataUrl: string) => {
    setCroppedImage(composedBeforeDataUrl); // This state now holds the "before" image for the slider
    setEnhancedImage(enhancedImageDataUrl);
    
    if (postCaptureDestination) {
      const destination = postCaptureDestination;
      setPostCaptureDestination(null); // Reset state after using it
      setScreen(destination);
      setActiveTab(destination);
    } else {
      setScreen(AppScreen.ENHANCE_RESULT);
    }
  }, [postCaptureDestination]);
  
  const handleProcessingError = useCallback(() => {
    alert('Processing failed — check network connection and try again.');
    goToCapture();
  }, [goToCapture]);

  const handleExport = useCallback((imageDataUrl: string) => {
    if (credits > 0) {
      setCredits(c => c - 1);
      const newHistoryItem: HistoryItem = {
        id: Date.now().toString(),
        thumbnail: imageDataUrl,
        original: croppedImage!,
        enhanced: enhancedImage!,
      };
      setHistory(h => [newHistoryItem, ...h]);
      setScreen(AppScreen.EXPORT);
    } else {
      alert("You're out of credits! Please purchase more to export.");
      setScreen(AppScreen.STORE);
      setActiveTab(AppScreen.STORE);
    }
  }, [credits, croppedImage, enhancedImage]);

  const navigateToTab = useCallback((tab: AppScreen) => {
    setPostCaptureDestination(null); // Reset any pending flow if user navigates manually
    setActiveTab(tab);
    setScreen(tab);
  }, []);
  
  const renderScreen = () => {
    switch (screen) {
      case AppScreen.ONBOARDING:
        return <OnboardingScreen onComplete={goToCapture} />;
      case AppScreen.CAPTURE:
        return <CaptureScreen onImageCaptured={handleImageCaptured} />;
      case AppScreen.CROP:
        return <CropScreen originalImage={originalImage!} onCropComplete={handleCropComplete} onRetake={goToCapture} />;
      case AppScreen.PROCESSING:
        return <ProcessingScreen originalImage={originalImage!} cropData={cropData!} onComplete={handleProcessingComplete} onError={handleProcessingError} />;
      case AppScreen.ENHANCE_RESULT:
        return <EnhanceResultScreen beforeImage={croppedImage!} afterImage={enhancedImage!} onContinue={goToEdit} onRetake={goToCapture} />;
      case AppScreen.EDIT:
        return (
          <EditScreen
            baseImage={enhancedImage!}
            onExport={handleExport}
            onBack={goToCapture}
          />
        );
      case AppScreen.EXPORT:
        return (
          <ExportScreen
             afterImage={history[0]?.thumbnail}
             beforeImage={history[0]?.original}
             onDone={resetToHome}
             onBackToEdit={goToEdit}
             onWatchFace={goToWatchFace}
             onIridology={goToIridology}
          />
        );
      case AppScreen.WATCHFACE:
        return (
            <WatchFaceScreen
                imageDataUrl={history[0]?.thumbnail}
                onBack={goToExport}
            />
        );
      case AppScreen.STORE:
        return <StoreScreen credits={credits} setCredits={setCredits} />;
      case AppScreen.GALLERY:
        return <GalleryScreen history={history} />;
      case AppScreen.SETTINGS:
        return <SettingsScreen />;
      case AppScreen.IRIDOLOGY:
        return <IridologyScreen enhancedImage={enhancedImage} onGoToCapture={startIridologyCaptureFlow} />;
      default:
        return <CaptureScreen onImageCaptured={handleImageCaptured} />;
    }
  };

  const showHeaderAndNav = useMemo(() => {
      return [AppScreen.CAPTURE, AppScreen.GALLERY, AppScreen.STORE, AppScreen.SETTINGS, AppScreen.IRIDOLOGY].includes(screen);
  }, [screen]);

  if (showSplash) {
    return <SplashScreen />;
  }

  return (
    <div className="h-full w-full bg-black flex flex-col font-sans">
      {showHeaderAndNav && <Header credits={credits} />}
      <main className="flex-grow overflow-y-auto min-h-0">
        {renderScreen()}
      </main>
      {showHeaderAndNav && <BottomNav activeTab={activeTab} setActiveTab={navigateToTab} />}
    </div>
  );
};

export default App;
