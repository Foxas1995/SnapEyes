import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { UploadIcon, SwitchCameraIcon, AutoAIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';
import { findEyeInFrame, IrisDetectionResult } from '../services/geminiService';
import { PhoneIcon, EyeIcon, FocusIcon, LightBulbIcon } from './common/Icons';

interface CaptureScreenProps {
  onImageCaptured: (imageDataUrl: string) => void;
}

const PhoneGuidanceAnimation: React.FC = () => (
  <div className="flex items-center space-x-1" aria-hidden="true">
    <style>{`
      @keyframes phone-move {
        0%, 100% { transform: translateX(0); }
        50% { transform: translateX(8px); }
      }
      .animate-phone-move {
        animation: phone-move 2.5s ease-in-out infinite;
      }
    `}</style>
    <div className="animate-phone-move">
      <PhoneIcon className="h-5 w-5 text-gray-300" />
    </div>
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12h10m-9-3l-3 3 3 3m11-3l-3 3 3 3" />
    </svg>
    <EyeIcon className="h-5 w-5 text-cyan-400" />
  </div>
);

type DetectionStatus = 'idle' | 'tracking' | 'locked';

const EyeBoundingBoxOverlay: React.FC<{ status: DetectionStatus; detection: IrisDetectionResult | null; facingMode: 'user' | 'environment' }> = ({ status, detection, facingMode }) => {
    const isVisible = status !== 'idle' && detection?.success && detection.box;
    const isLocked = status === 'locked';

    if (!isVisible || !detection?.box) {
        return null;
    }

    const { xMin, yMin, xMax, yMax } = detection.box;

    // For the front-facing camera ('user'), the video preview is mirrored via CSS.
    // The AI detection runs on the un-mirrored video stream.
    // Therefore, we must flip the horizontal (x) coordinates of the bounding box
    // to correctly position it on the mirrored preview.
    const displayXMin = facingMode === 'user' ? (1 - xMax) : xMin;

    return (
        <div 
            className={`absolute border-2 rounded-lg transition-all duration-300 pointer-events-none
                ${isLocked ? 'border-cyan-400 animate-pulse' : 'border-white border-dashed'}
                ${isVisible ? 'opacity-100' : 'opacity-0'}
            `}
            style={{
                left: `${displayXMin * 100}%`,
                top: `${yMin * 100}%`,
                width: `${(xMax - xMin) * 100}%`,
                height: `${(yMax - yMin) * 100}%`,
            }}
        />
    );
};


const CaptureScreen: React.FC<CaptureScreenProps> = ({ onImageCaptured }) => {
  const { t } = useLocalization();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [facingMode, setFacingMode] = useState<'user' | 'environment'>('user');
  const [showTutorial, setShowTutorial] = useState(false);

  // Auto-capture state
  const [autoCaptureEnabled, setAutoCaptureEnabled] = useState(false);
  const [detectionStatus, setDetectionStatus] = useState<DetectionStatus>('idle');
  const [detectionResult, setDetectionResult] = useState<IrisDetectionResult | null>(null);
  const [zoom, setZoom] = useState(1);
  const [countdown, setCountdown] = useState<number | null>(null);

  const analysisIntervalRef = useRef<number | null>(null);
  const countdownTimeoutsRef = useRef<number[]>([]);
  const steadyTimeoutRef = useRef<number | null>(null);
  const countdownInProgress = useRef(false);
  const isAnalyzingRef = useRef(false);
  const audioContextRef = useRef<AudioContext | null>(null);


  useEffect(() => {
    try {
      const tutorialSeen = localStorage.getItem('snapeyes_capture_tutorial_seen');
      if (!tutorialSeen) {
        setShowTutorial(true);
      }
    } catch (e) {
      console.warn('Could not access localStorage for tutorial status.');
    }
  }, []);

  const handleDismissTutorial = useCallback(() => {
    try {
      localStorage.setItem('snapeyes_capture_tutorial_seen', 'true');
    } catch (e) {
      console.warn('Could not save tutorial status to localStorage.');
    }
    setShowTutorial(false);
  }, []);


  useEffect(() => {
    let mediaStream: MediaStream | null = null;
    let isMounted = true;

    const startCamera = async () => {
      setCameraReady(false);
      setError(null);
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: facingMode,
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          }
        });

        if (!isMounted) {
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
            }
            return;
        }

        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          videoRef.current.onloadedmetadata = () => {
            if (isMounted) {
                setCameraReady(true);
            }
          };
        }
      } catch (err) {
        console.error("Error accessing camera: ", err);
        if (isMounted) {
            setError(t('cameraError'));
        }
      }
    };

    startCamera();

    return () => {
      isMounted = false;
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode, t]);

  const stopStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  }, [stream]);

  const initAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
        try {
            const context = new (window.AudioContext || (window as any).webkitAudioContext)();
            if (context.state === 'suspended') {
                context.resume();
            }
            audioContextRef.current = context;
        } catch (e) {
            console.error("Web Audio API is not supported in this browser.");
        }
    } else if (audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume();
    }
  }, []);

  const handleCapture = useCallback(() => {
    initAudioContext();
    if (videoRef.current && canvasRef.current && cameraReady) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      const videoWidth = video.videoWidth;
      const videoHeight = video.videoHeight;
      
      canvas.width = videoWidth;
      canvas.height = videoHeight;
      
      const context = canvas.getContext('2d');
      if (context) {
        // The preview is mirrored using CSS transform on the video element for a natural selfie experience.
        // The raw video stream is not mirrored. We draw the raw stream directly to the canvas
        // to produce a final image that is correctly oriented (not mirrored), as if someone
        // else was taking the picture.
        context.drawImage(video, 0, 0, videoWidth, videoHeight);
        
        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
        onImageCaptured(dataUrl);
        stopStream();
      }
    }
  }, [onImageCaptured, cameraReady, stopStream, initAudioContext]);

  const handleToggleCamera = useCallback(() => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  }, []);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (typeof e.target?.result === 'string') {
          onImageCaptured(e.target.result);
          stopStream();
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // --- Auto Capture Logic ---
  
  const playBeep = useCallback((frequency: number, duration: number) => {
    const context = audioContextRef.current;
    if (!context) return;
    if (context.state === 'suspended') context.resume();

    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    gainNode.gain.setValueAtTime(0, context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, context.currentTime + 0.01);

    oscillator.frequency.setValueAtTime(frequency, context.currentTime);
    oscillator.type = 'sine';
    
    oscillator.start(context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.00001, context.currentTime + duration / 1000);
    oscillator.stop(context.currentTime + duration / 1000);
  }, []);

  const clearCountdownTimeouts = useCallback(() => {
      countdownTimeoutsRef.current.forEach(clearTimeout);
      countdownTimeoutsRef.current = [];
  }, []);

  const resetAutoCaptureState = useCallback(() => {
      if (analysisIntervalRef.current) clearInterval(analysisIntervalRef.current);
      if (steadyTimeoutRef.current) clearTimeout(steadyTimeoutRef.current);
      clearCountdownTimeouts();
      countdownInProgress.current = false;
      analysisIntervalRef.current = null;
      steadyTimeoutRef.current = null;
      setDetectionStatus('idle');
      setDetectionResult(null);
      setCountdown(null);
      setZoom(1);
  }, [clearCountdownTimeouts]);

  const handleToggleAutoCapture = useCallback(() => {
    initAudioContext();
    setAutoCaptureEnabled(currentValue => {
        const newValue = !currentValue;
        if (newValue === false) { // Toggling OFF
            resetAutoCaptureState();
        } else {
            setDetectionStatus('idle');
        }
        return newValue;
    });
  }, [initAudioContext, resetAutoCaptureState]);

  const analyzeFrame = useCallback(async () => {
    if (isAnalyzingRef.current || !videoRef.current || !canvasRef.current || !autoCaptureEnabled) return;
    isAnalyzingRef.current = true;
    
    try {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        canvas.width = 640;
        canvas.height = (video.videoHeight / video.videoWidth) * 640;
        
        const context = canvas.getContext('2d');
        if (!context) {
            isAnalyzingRef.current = false;
            return;
        }

        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
        const base64Data = dataUrl.split(',')[1];
        
        const result = await findEyeInFrame(base64Data);

        if (result.success && result.box) {
            setDetectionResult(result);

            if (detectionStatus !== 'locked') {
              setDetectionStatus('tracking');
            }
            
            const boxWidthNormalized = result.box.xMax - result.box.xMin;
            const targetBoxWidth = 0.40; // Target width of the box relative to screen
            const newZoom = Math.min(Math.max(1, targetBoxWidth / boxWidthNormalized), 4);
            setZoom(z => z + (newZoom - z) * 0.2); // Smooth zoom

            if (steadyTimeoutRef.current) clearTimeout(steadyTimeoutRef.current);
            if (!countdownInProgress.current) {
                steadyTimeoutRef.current = window.setTimeout(() => {
                    setDetectionStatus('locked');
                }, 500);
            }
        } else {
             if (steadyTimeoutRef.current) clearTimeout(steadyTimeoutRef.current);
             setDetectionStatus('idle');
             setDetectionResult(null);
             setZoom(z => z + (1 - z) * 0.2); // Smooth zoom out
        }

    } catch (error) {
        console.error("Auto-capture analysis error:", error);
        setDetectionStatus('idle');
        setZoom(1);
    } finally {
        isAnalyzingRef.current = false;
    }
  }, [autoCaptureEnabled, detectionStatus]);

  useEffect(() => {
    if (autoCaptureEnabled && cameraReady) {
        analysisIntervalRef.current = window.setInterval(analyzeFrame, 750);
    } else {
        if (analysisIntervalRef.current) clearInterval(analysisIntervalRef.current);
    }
    return () => {
        if (analysisIntervalRef.current) clearInterval(analysisIntervalRef.current);
    };
  }, [autoCaptureEnabled, cameraReady, analyzeFrame]);

  useEffect(() => {
    if (detectionStatus === 'locked' && autoCaptureEnabled && !countdownInProgress.current) {
        countdownInProgress.current = true;
        
        playBeep(440, 100);
        setCountdown(2);

        const t1 = window.setTimeout(() => {
            setCountdown(1);
            playBeep(440, 100);
        }, 1000);
        
        const t2 = window.setTimeout(() => {
            setCountdown(null); 
            playBeep(880, 200);
            handleCapture();
            countdownInProgress.current = false;
        }, 2000);

        countdownTimeoutsRef.current = [t1, t2];

    } else if (detectionStatus !== 'locked' && countdownInProgress.current) {
        clearCountdownTimeouts();
        setCountdown(null);
        countdownInProgress.current = false;
    }
    
    return () => {
        clearCountdownTimeouts();
    };
  }, [detectionStatus, autoCaptureEnabled, handleCapture, playBeep, clearCountdownTimeouts]);


  const topHintText = useMemo(() => {
    if (autoCaptureEnabled) {
      switch (detectionStatus) {
        case 'locked': return t('holdSteady');
        case 'tracking': return t('eyeDetectedHoldSteady');
        case 'idle':
        default: return t('autoCaptureHint');
      }
    }
    return t('cameraHint');
  }, [autoCaptureEnabled, detectionStatus, t]);


  const TutorialOverlay = ({ onDismiss }: { onDismiss: () => void }) => {
    const { t } = useLocalization();
    return (
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center p-6 animate-in fade-in duration-300">
        <style>{`
          @keyframes tutorial-phone-move {
            0%, 100% { transform: translateX(-30px); }
            50% { transform: translateX(30px); }
          }
          @keyframes focus-pulse {
            0%, 100% { stroke-opacity: 0.2; transform: scale(0.95); }
            50% { stroke-opacity: 1; transform: scale(1.05); }
          }
          .animate-tutorial-phone-move {
            animation: tutorial-phone-move 3s ease-in-out infinite;
          }
          .animate-focus-pulse {
            animation: focus-pulse 3s ease-in-out infinite;
            transform-origin: center;
          }
          .animate-in { animation-duration: 300ms; }
          .fade-in { animation-name: fadeIn; }
          @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        `}</style>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 w-full max-w-sm text-center shadow-2xl">
          <h2 className="text-2xl font-bold text-cyan-400 mb-4">{t('tutorialTitle')}</h2>
          
          <div className="relative h-24 my-6 flex items-center justify-center">
            <div className="absolute w-full max-w-[200px] flex items-center justify-between">
              <div className="animate-tutorial-phone-move relative" style={{left: '50%', transform: 'translateX(-50%)'}}>
                  <PhoneIcon className="w-10 h-10 text-gray-300" />
              </div>
               <div className="relative">
                  <EyeIcon className="w-12 h-12 text-cyan-400" />
                  <FocusIcon className="absolute -inset-2 w-16 h-16 text-cyan-400 animate-focus-pulse" />
              </div>
            </div>
          </div>

          <ul className="space-y-4 text-left text-gray-200">
            <li className="flex items-center space-x-4">
              <LightBulbIcon className="w-8 h-8 text-cyan-400 flex-shrink-0" />
              <p>{t('tutorialStep1')}</p>
            </li>
            <li className="flex items-center space-x-4">
              <PhoneIcon className="w-8 h-8 text-cyan-400 flex-shrink-0" />
              <p>{t('tutorialStep2')}</p>
            </li>
            <li className="flex items-center space-x-4">
              <FocusIcon className="w-8 h-8 text-cyan-400 flex-shrink-0" />
              <p>{t('tutorialStep3')}</p>
            </li>
          </ul>

          <button
            onClick={onDismiss}
            className="mt-8 w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-4 rounded-full transition-transform transform hover:scale-105"
          >
            {t('tutorialGotIt')}
          </button>
        </div>
      </div>
    );
  };
  
  return (
    <div className="relative h-full w-full flex flex-col items-center justify-center bg-black overflow-hidden">
      {showTutorial && <TutorialOverlay onDismiss={handleDismissTutorial} />}

      {/* Video and Guide Container */}
      <div className="absolute inset-0 w-full h-full">
         <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover transition-transform duration-500 ease-out ${facingMode === 'user' ? 'transform -scale-x-100' : ''}`}
            style={{ transform: `scale(${zoom})` }}
        />
        <EyeBoundingBoxOverlay status={detectionStatus} detection={detectionResult} facingMode={facingMode} />
      </div>
      
      <canvas ref={canvasRef} className="hidden" />
      <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />

      {/* Error Display */}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-30 p-8 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-white">{error}</p>
             <button
                onClick={handleToggleCamera}
                className="mt-6 px-6 py-2 bg-cyan-600 rounded-full text-white font-semibold"
            >
                {t('tryOtherCamera')}
            </button>
        </div>
      )}

      {/* Loading/Waiting for Camera */}
      {!cameraReady && !error && (
         <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-20">
            <svg className="animate-spin h-10 w-10 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-white mt-4">{t('startingCamera')}</p>
         </div>
      )}

      {/* Countdown Overlay */}
      {countdown !== null && (
        <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
          <div className="text-white font-bold text-9xl drop-shadow-2xl animate-in fade-in zoom-in">
            {countdown}
          </div>
        </div>
      )}

       {/* Top Controls */}
       <div className="absolute top-0 right-0 p-8 z-20 flex items-center space-x-2">
        <button
            onClick={handleToggleAutoCapture}
            className={`p-3 bg-black/40 rounded-full backdrop-blur-md transition-all duration-200 ease-in-out transform hover:scale-110 active:scale-95 ${autoCaptureEnabled ? 'text-cyan-400' : 'text-white'}`}
            aria-label={t('autoCapture')}
        >
            <AutoAIcon className="w-6 h-6" />
        </button>
        <button
            onClick={handleToggleCamera}
            className="p-3 bg-black/40 rounded-full text-white backdrop-blur-md transition-transform duration-200 ease-in-out transform hover:scale-110 active:scale-95"
            aria-label="Switch camera"
        >
            <SwitchCameraIcon className="w-6 h-6" />
        </button>
      </div>
      
      {/* Top Hint */}
      <div className="absolute top-16 left-0 right-0 p-4 z-20 pointer-events-none flex justify-center">
         <div className="inline-flex items-center space-x-3 bg-black/50 backdrop-blur-md text-white text-sm rounded-full px-4 py-2">
            {!autoCaptureEnabled && <PhoneGuidanceAnimation />}
            <span>{topHintText}</span>
         </div>
      </div>
      
      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-8 flex items-center justify-center z-20">
        <div className="flex-1 flex justify-start pl-4">
             <button
                onClick={handleUploadClick}
                className="flex flex-col items-center text-white font-semibold transition-transform duration-200 ease-in-out transform hover:scale-110 active:scale-95"
                aria-label="Upload from library"
            >
                <div className="p-3 bg-black/40 rounded-full backdrop-blur-md mb-1">
                     <UploadIcon className="w-6 h-6" />
                </div>
                <span className="text-xs drop-shadow-md">{t('upload')}</span>
            </button>
        </div>
        <div className="flex flex-col items-center">
            <button
            onClick={handleCapture}
            disabled={!cameraReady || !!error}
            className="w-20 h-20 bg-white rounded-full border-4 border-black ring-4 ring-white/50 focus:outline-none focus:ring-cyan-400 transition-transform duration-200 ease-in-out transform hover:scale-110 active:scale-95 disabled:opacity-50 disabled:scale-100"
            aria-label="Capture photo"
            >
            </button>
        </div>
        <div className="flex-1"></div>
      </div>
    </div>
  );
};

export default CaptureScreen;