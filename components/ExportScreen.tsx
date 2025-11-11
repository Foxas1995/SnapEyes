

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { DownloadIcon, PlayIcon, WatchIcon, ShareIcon, XIcon, IridologyIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';
import { ComparisonSlider } from './common/Slider';

interface ExportScreenProps {
  beforeImage: string | null;
  afterImage: string | null;
  onDone: () => void;
  onBackToEdit: () => void;
  onWatchFace: () => void;
  onIridology: () => void;
}

interface VideoFormat {
    mime: string;
    ext: string;
    label: string;
}

type AspectRatio = '1:1' | '9:16' | '16:9';

const ExportScreen: React.FC<ExportScreenProps> = ({ beforeImage, afterImage, onDone, onBackToEdit, onWatchFace, onIridology }) => {
  const { t } = useLocalization();
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [showFormatModal, setShowFormatModal] = useState(false);
  const [showAspectRatioModal, setShowAspectRatioModal] = useState(false);
  const [showDurationModal, setShowDurationModal] = useState(false);
  const [selectedAspectRatio, setSelectedAspectRatio] = useState<AspectRatio>('1:1');
  const [selectedDuration, setSelectedDuration] = useState<number>(4000);
  const [supportedFormats, setSupportedFormats] = useState<VideoFormat[]>([]);

  useEffect(() => {
      const checkFormats = () => {
          const formatsToCheck: VideoFormat[] = [
              { mime: 'video/mp4', ext: 'mp4', label: 'MP4 (Best for Social)' },
              { mime: 'video/webm;codecs=vp9', ext: 'webm', label: 'WebM (High Quality)' },
              { mime: 'video/webm', ext: 'webm', label: 'WebM (Standard)' },
          ];
          const supported = formatsToCheck.filter(f => MediaRecorder.isTypeSupported(f.mime));
          // Deduplicate based on extension if multiple mime types map to same extension (rare but possible with different codecs)
          const unique = supported.filter((v,i,a)=>a.findIndex(t=>(t.ext === v.ext))===i);
          setSupportedFormats(supported.length > 0 ? supported : unique);
      };
      checkFormats();
  }, []);

  const handleDownload = (format: 'png' | 'jpeg') => {
    if (!afterImage) return;
    const link = document.createElement('a');
    link.href = afterImage;
    link.download = `snapeyes_${Date.now()}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  const handleShare = async () => {
      if(!afterImage) return;
      try {
        const response = await fetch(afterImage);
        const blob = await response.blob();
        const file = new File([blob], `snapeyes_${Date.now()}.png`, { type: 'image/png' });

        if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                title: 'My SnapEyes Photo',
                text: 'Check out my AI-enhanced iris photo from SnapEyes!',
                files: [file]
            });
        } else {
             alert('Image sharing not supported on this browser. Downloading instead.');
             handleDownload('png');
        }
      } catch(error) {
          console.error("Share failed:", error);
      }
  }

  const handleSaveVideoClick = () => {
      if (!beforeImage || !afterImage) return;
      if (supportedFormats.length > 0) {
          setShowAspectRatioModal(true);
      } else {
          alert("Sorry, video generation is not supported on this device/browser.");
      }
  };

  const handleAspectRatioSelected = (aspectRatio: AspectRatio) => {
    setSelectedAspectRatio(aspectRatio);
    setShowAspectRatioModal(false);
    setShowDurationModal(true);
  };

  const handleDurationSelected = (duration: number) => {
    setSelectedDuration(duration);
    setShowDurationModal(false);
    if (supportedFormats.length > 1) {
        setShowFormatModal(true);
    } else if (supportedFormats.length === 1) {
        generateAndDownloadVideo(supportedFormats[0], selectedAspectRatio, duration);
    }
  };

  const generateAndDownloadVideo = async (format: VideoFormat, aspectRatio: AspectRatio, duration: number) => {
      if (!beforeImage || !afterImage) return;
      if (isGeneratingVideo) return;

      setShowFormatModal(false);
      setIsGeneratingVideo(true);
      try {
          const videoUrl = await generateComparisonVideo(beforeImage, afterImage, format.mime, aspectRatio, duration);
          const link = document.createElement('a');
          link.href = videoUrl;
          link.download = `snapeyes_anim_${Date.now()}.${format.ext}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(videoUrl);
      } catch (error) {
          console.error("Animation generation failed:", error);
          alert("Sorry, could not generate animation on this device.");
      } finally {
          setIsGeneratingVideo(false);
      }
  };

  return (
    <div className="flex flex-col min-h-full p-6 bg-gray-900 text-center relative">
      <h2 className="text-3xl font-bold mb-4">{t('exportTitle')}</h2>
      <p className="text-gray-400 mb-6">{t('exportSub')}</p>
      
      <div className="flex-grow flex flex-col items-center justify-center mb-6">
        {beforeImage && afterImage ? (
            <div className="w-full max-w-xs aspect-square relative rounded-lg overflow-hidden shadow-2xl shadow-cyan-500/20">
                <ComparisonSlider before={beforeImage} after={afterImage} />
            </div>
        ) : afterImage ? (
             <img src={afterImage} alt="Final SnapEyes Photo" className="max-w-full max-h-64 rounded-lg shadow-2xl shadow-cyan-500/20" />
        ) : null}
        {beforeImage && afterImage && (
             <p className="text-xs text-gray-500 mt-3">{t('dragToCompare')}</p>
        )}
      </div>
      
      <div className="w-full max-w-sm mx-auto space-y-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <ExportButton icon={<DownloadIcon className="w-6 h-6" />} label={t('savePng')} onClick={() => handleDownload('png')} />
          <ExportButton icon={<ShareIcon className="w-6 h-6" />} label={t('share')} onClick={handleShare} />
          <ExportButton 
              icon={isGeneratingVideo ? <div className="w-6 h-6 rounded-full border-2 border-t-cyan-500 animate-spin"/> : <PlayIcon className="w-6 h-6" />} 
              label={isGeneratingVideo ? t('saving') : t('createAnimation')} 
              onClick={handleSaveVideoClick}
              disabled={isGeneratingVideo}
          />
          <ExportButton icon={<WatchIcon className="w-6 h-6" />} label={t('createWatchFace')} onClick={onWatchFace} />
        </div>
        <button
            onClick={onIridology}
            className="bg-cyan-900/50 border border-cyan-500 p-4 rounded-lg w-full flex flex-col items-center justify-center space-y-2 transition-colors hover:bg-cyan-800/50"
        >
            <IridologyIcon className="w-6 h-6 text-cyan-400" />
            <span className="text-sm text-cyan-300 font-semibold">{t('analyzeMyIris')}</span>
        </button>
      </div>

      <div className="w-full max-w-sm mx-auto flex flex-col gap-3">
         <button
            onClick={onBackToEdit}
            className="w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-4 rounded-full transition-transform duration-200 ease-in-out transform hover:scale-105"
        >
            {t('tryAnotherEffect')}
        </button>
        <button
            onClick={onDone}
            className="w-full bg-gray-800 hover:bg-gray-700 text-white font-bold py-3 px-4 rounded-full transition-colors"
        >
            {t('done')}
        </button>
      </div>

      {/* Aspect Ratio Selection Modal */}
      {showAspectRatioModal && (
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-gray-900 p-6 rounded-2xl w-full max-w-sm border border-gray-800 shadow-2xl animate-in fade-in zoom-in duration-200">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-bold text-white">{t('aspectRatioTitle')}</h3>
                      <button onClick={() => setShowAspectRatioModal(false)} className="text-gray-400 hover:text-white">
                          <XIcon className="w-6 h-6" />
                      </button>
                  </div>
                  <div className="space-y-3">
                        <button onClick={() => handleAspectRatioSelected('9:16')} className="w-full flex items-center p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors text-left">
                            <span className="font-bold text-cyan-400 flex-grow">{t('aspectRatio916')}</span>
                            <div className="w-8 h-14 bg-gray-700 border-2 border-gray-600 rounded-md"></div>
                        </button>
                        <button onClick={() => handleAspectRatioSelected('1:1')} className="w-full flex items-center p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors text-left">
                            <span className="font-bold text-cyan-400 flex-grow">{t('aspectRatio11')}</span>
                             <div className="w-12 h-12 bg-gray-700 border-2 border-gray-600 rounded-md"></div>
                        </button>
                        <button onClick={() => handleAspectRatioSelected('16:9')} className="w-full flex items-center p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors text-left">
                           <span className="font-bold text-cyan-400 flex-grow">{t('aspectRatio169')}</span>
                           <div className="w-14 h-8 bg-gray-700 border-2 border-gray-600 rounded-md"></div>
                        </button>
                  </div>
              </div>
          </div>
      )}

      {/* Duration Selection Modal */}
      {showDurationModal && (
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-gray-900 p-6 rounded-2xl w-full max-w-sm border border-gray-800 shadow-2xl animate-in fade-in zoom-in duration-200">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-bold text-white">{t('durationTitle')}</h3>
                      <button onClick={() => setShowDurationModal(false)} className="text-gray-400 hover:text-white">
                          <XIcon className="w-6 h-6" />
                      </button>
                  </div>
                  <div className="space-y-3">
                      <button onClick={() => handleDurationSelected(2000)} className="w-full text-left p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors font-bold text-cyan-400">
                          {t('duration2s')}
                      </button>
                      <button onClick={() => handleDurationSelected(4000)} className="w-full text-left p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors font-bold text-cyan-400">
                          {t('duration4s')}
                      </button>
                      <button onClick={() => handleDurationSelected(6000)} className="w-full text-left p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors font-bold text-cyan-400">
                          {t('duration6s')}
                      </button>
                  </div>
              </div>
          </div>
      )}

      {/* Video Format Selection Modal */}
      {showFormatModal && (
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-gray-900 p-6 rounded-2xl w-full max-w-sm border border-gray-800 shadow-2xl animate-in fade-in zoom-in duration-200">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-bold text-white">{t('videoFormatTitle')}</h3>
                      <button onClick={() => setShowFormatModal(false)} className="text-gray-400 hover:text-white">
                          <XIcon className="w-6 h-6" />
                      </button>
                  </div>
                  <div className="space-y-3">
                      {supportedFormats.map((format) => (
                          <button
                              key={format.mime}
                              onClick={() => generateAndDownloadVideo(format, selectedAspectRatio, selectedDuration)}
                              className="w-full flex flex-col items-start p-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors text-left"
                          >
                              <span className="font-bold text-cyan-400">{format.label}</span>
                              <span className="text-xs text-gray-500">.{format.ext} ({format.mime.split(';')[0]})</span>
                          </button>
                      ))}
                  </div>
              </div>
          </div>
      )}
    </div>
  );
};

const ExportButton: React.FC<{icon: React.ReactNode, label: string, onClick: () => void, disabled?: boolean}> = ({ icon, label, onClick, disabled }) => (
    <button 
        onClick={onClick} 
        disabled={disabled}
        className={`bg-gray-800 p-4 rounded-lg flex flex-col items-center justify-center space-y-2 transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-700'}`}
    >
        {icon}
        <span className="text-sm">{label}</span>
    </button>
);

async function generateComparisonVideo(beforeSrc: string, afterSrc: string, mimeType: string, aspectRatio: AspectRatio, duration: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return reject(new Error("Could not get canvas context"));

      const beforeImg = new Image();
      const afterImg = new Image();

      let loaded = 0;
      const onLoaded = () => {
        loaded++;
        if (loaded === 2) startRecording();
      };
      
      beforeImg.onload = onLoaded;
      afterImg.onload = onLoaded;
      beforeImg.onerror = (e) => reject(new Error(`Failed to load before image: ${e}`));
      afterImg.onerror = (e) => reject(new Error(`Failed to load after image: ${e}`));
      
      beforeImg.crossOrigin = "anonymous";
      afterImg.crossOrigin = "anonymous";
      
      beforeImg.src = beforeSrc;
      afterImg.src = afterSrc;

      function startRecording() {
          switch (aspectRatio) {
              case '9:16':
                  canvas.width = 1080;
                  canvas.height = 1920;
                  break;
              case '16:9':
                  canvas.width = 1920;
                  canvas.height = 1080;
                  break;
              case '1:1':
              default:
                  canvas.width = 1080;
                  canvas.height = 1080;
                  break;
          }

          const drawSize = Math.min(canvas.width, canvas.height);
          const xOffset = (canvas.width - drawSize) / 2;
          const yOffset = (canvas.height - drawSize) / 2;
          
          const FPS = 30; // Use a constant frame rate for better compatibility

          // Create a silent audio track to add to the video, as some platforms require it.
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const oscillator = audioContext.createOscillator();
          const gainNode = audioContext.createGain();
          gainNode.gain.setValueAtTime(0, audioContext.currentTime);
          const audioDestination = audioContext.createMediaStreamDestination();
          oscillator.connect(gainNode);
          gainNode.connect(audioDestination);
          oscillator.start();
          const audioTrack = audioDestination.stream.getAudioTracks()[0];
          
          const videoStream = canvas.captureStream(FPS);
          const videoTrack = videoStream.getVideoTracks()[0];
          
          const combinedStream = new MediaStream([videoTrack, audioTrack]);

          let recorder: MediaRecorder;
          try {
             recorder = new MediaRecorder(combinedStream, { mimeType, videoBitsPerSecond: 2500000 });
          } catch (e) {
             console.warn(`Preferred mimeType ${mimeType} failed, falling back to default.`);
             recorder = new MediaRecorder(combinedStream);
          }
          
          const chunks: Blob[] = [];
          recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
          
          recorder.onstop = () => {
              combinedStream.getTracks().forEach(track => track.stop());
              audioContext.close();
              if (chunks.length === 0) {
                return reject(new Error("Video recording failed: No data chunks were recorded."));
              }
              const blob = new Blob(chunks, { type: recorder.mimeType || mimeType });
              resolve(URL.createObjectURL(blob));
          };

          recorder.start();

          const animationDuration = Math.max(1000, duration - 1000); // e.g. 3000ms for a 4000ms duration
          const totalDuration = duration;
          let frameCount = 0;
          const totalFrames = (totalDuration / 1000) * FPS;
          
          const animationInterval = setInterval(() => {
              const elapsed = frameCount * (1000 / FPS);
              
              ctx.fillStyle = 'black';
              ctx.fillRect(0, 0, canvas.width, canvas.height);

              let sliderPos;
              if (elapsed < animationDuration) {
                  // Use an ease-in-out function for smooth acceleration and deceleration
                  const progress = elapsed / animationDuration;
                  sliderPos = (1 - Math.cos(progress * Math.PI)) / 2;
              } else {
                  sliderPos = 1; // Hold on the final "after" frame
              }

              ctx.drawImage(beforeImg, 0, 0, beforeImg.naturalWidth, beforeImg.naturalHeight, xOffset, yOffset, drawSize, drawSize);
              
              const sliderCanvasX = xOffset + (drawSize * sliderPos);

              ctx.save();
              ctx.beginPath();
              ctx.rect(xOffset, yOffset, sliderCanvasX - xOffset, drawSize);
              ctx.clip();
              ctx.drawImage(afterImg, 0, 0, afterImg.naturalWidth, afterImg.naturalHeight, xOffset, yOffset, drawSize, drawSize);
              ctx.restore();
              
              // Draw the slider line only during the animation phase
              if (elapsed < animationDuration) {
                  ctx.beginPath();
                  ctx.moveTo(sliderCanvasX, yOffset);
                  ctx.lineTo(sliderCanvasX, yOffset + drawSize);
                  ctx.strokeStyle = 'white';
                  ctx.lineWidth = Math.max(2, drawSize * 0.005); 
                  ctx.stroke();
              }

              frameCount++;

              if (frameCount >= totalFrames) {
                  clearInterval(animationInterval);
                   if (recorder.state === 'recording') {
                       recorder.stop();
                   }
              }
          }, 1000 / FPS);
      }
    });
}

export default ExportScreen;
