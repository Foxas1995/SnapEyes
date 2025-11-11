

import React, { useState, useCallback, useRef } from 'react';
import { detectIris } from '../services/geminiService';
import { EyeIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';
import { CropData } from '../types';

interface CropScreenProps {
  originalImage: string;
  onCropComplete: (cropData: CropData) => void;
  onRetake: () => void;
}

const CropScreen: React.FC<CropScreenProps> = ({ originalImage, onCropComplete, onRetake }) => {
  const { t } = useLocalization();
  const [status, setStatus] = useState<'loading' | 'editing' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  
  const [cropParams, setCropParams] = useState({ x: 0, y: 0, radius: 100 });
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const dragStartOffset = useRef({ x: 0, y: 0 });

  const getInitialCrop = useCallback(async () => {
    if (!imageRef.current) {
        setErrorMessage("Image reference could not be found.");
        setStatus('error');
        return;
    }

    const img = imageRef.current;
    const currentImageSize = { width: img.clientWidth, height: img.clientHeight };
    setImageSize(currentImageSize);

    const base64Data = originalImage.split(',')[1];

    try {
        const irisDetectionResult = await detectIris(base64Data);

        if (!irisDetectionResult.success || !irisDetectionResult.centerX || !irisDetectionResult.centerY || !irisDetectionResult.radius) {
            setErrorMessage(irisDetectionResult.error || 'An unknown error occurred.');
            setStatus('error');
            return;
        }
        
        const { centerX, centerY, radius } = irisDetectionResult;
        const newCropParams = {
            x: centerX * currentImageSize.width,
            y: centerY * currentImageSize.height,
            radius: radius * currentImageSize.width,
        };
        setCropParams(newCropParams);
        setStatus('editing');

    } catch (error) {
        console.error(error);
        setErrorMessage(error instanceof Error ? error.message : 'An unknown error occurred.');
        setStatus('error');
    }
  }, [originalImage]);

  const getPointerPosition = (e: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const rect = containerRef.current.getBoundingClientRect();
    const touch = 'touches' in e ? e.touches[0] : null;
    return {
      x: (touch ? touch.clientX : (e as MouseEvent).clientX) - rect.left,
      y: (touch ? touch.clientY : (e as MouseEvent).clientY) - rect.top,
    };
  }

  const handleDragMove = useCallback((e: MouseEvent | TouchEvent) => {
    if (!isDragging.current) return;
    
    // Prevent the page from scrolling on touch devices while dragging.
    if (e.cancelable) e.preventDefault();

    const pos = getPointerPosition(e);
    
    setCropParams(prev => {
      const newX = Math.max(prev.radius, Math.min(pos.x - dragStartOffset.current.x, imageSize.width - prev.radius));
      const newY = Math.max(prev.radius, Math.min(pos.y - dragStartOffset.current.y, imageSize.height - prev.radius));
      return { ...prev, x: newX, y: newY };
    });
  }, [imageSize]);

  const handleDragEnd = useCallback(() => {
    isDragging.current = false;
    window.removeEventListener('mousemove', handleDragMove);
    window.removeEventListener('touchmove', handleDragMove);
    window.removeEventListener('mouseup', handleDragEnd);
    window.removeEventListener('touchend', handleDragEnd);
  }, [handleDragMove]);

  const handleDragStart = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    isDragging.current = true;
    const pos = getPointerPosition(e);
    dragStartOffset.current = {
        x: pos.x - cropParams.x,
        y: pos.y - cropParams.y,
    };
    
    window.addEventListener('mousemove', handleDragMove);
    window.addEventListener('touchmove', handleDragMove, { passive: false });
    window.addEventListener('mouseup', handleDragEnd);
    window.addEventListener('touchend', handleDragEnd);

  }, [cropParams.x, cropParams.y, handleDragEnd, handleDragMove]);

  const handleRadiusChange = useCallback((newRadius: number) => {
    setCropParams(prev => {
        const clampedRadius = Math.max(20, Math.min(newRadius, Math.floor(Math.min(imageSize.width, imageSize.height) / 2)));
        const newX = Math.max(clampedRadius, Math.min(prev.x, imageSize.width - clampedRadius));
        const newY = Math.max(clampedRadius, Math.min(prev.y, imageSize.height - clampedRadius));
        return { x: newX, y: newY, radius: clampedRadius };
    });
  }, [imageSize]);
  
  const handleContinue = useCallback(() => {
    if (!imageSize.width || !imageSize.height) return;

    const normalizedCropData: CropData = {
      centerX: cropParams.x / imageSize.width,
      centerY: cropParams.y / imageSize.height,
      radius: cropParams.radius / imageSize.width, // Radius is relative to image width
    };
    onCropComplete(normalizedCropData);
  }, [cropParams, imageSize, onCropComplete]);

  return (
    <div className="min-h-full w-full bg-gray-900 flex flex-col">
      {status === 'loading' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center h-full text-center p-8 bg-gray-900 z-20">
          <EyeIcon className="w-24 h-24 text-cyan-400 animate-pulse" />
          <h2 className="text-xl font-bold mt-8">{t('locatingIris')}</h2>
          <p className="text-gray-400 mt-2">{t('locatingIrisSub')}</p>
        </div>
      )}
      {status === 'error' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center h-full text-center p-8 bg-gray-900 z-20">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-bold mt-6">{t('detectionFailed')}</h2>
          <p className="text-gray-400 mt-2 max-w-sm">{errorMessage}</p>
          <button
              onClick={onRetake}
              className="mt-8 w-full max-w-xs bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-4 rounded-full transition-transform duration-200 ease-in-out transform hover:scale-105"
          >
              {t('retakePhoto')}
          </button>
        </div>
      )}

      <div className={`p-6 text-center flex-shrink-0 transition-opacity duration-300 ${status === 'editing' ? 'opacity-100' : 'opacity-0'}`}>
          <h2 className="text-3xl font-bold mb-2">{t('adjustCrop')}</h2>
          <p className="text-gray-400">{t('adjustCropSub')}</p>
      </div>

      <div ref={containerRef} className="flex-grow flex items-center justify-center my-4 relative">
          <img 
            ref={imageRef} 
            src={originalImage} 
            alt="Eye to be cropped" 
            className={`max-w-full max-h-full object-contain select-none transition-opacity duration-300 ${status === 'editing' ? 'opacity-100' : 'opacity-0'}`}
            onLoad={getInitialCrop}
            onError={() => { setErrorMessage("The image file could not be loaded."); setStatus('error');}}
          />
          {status === 'editing' && imageSize.width > 0 && (
            <>
              <div 
                  className="absolute inset-0 bg-black/60 pointer-events-none" 
                  style={{ 
                      clipPath: `path('M0 0 H${imageSize.width} V${imageSize.height} H0z M${cropParams.x} ${cropParams.y} m-${cropParams.radius} 0 a${cropParams.radius},${cropParams.radius} 0 1,0 ${cropParams.radius * 2},0 a${cropParams.radius},${cropParams.radius} 0 1,0 -${cropParams.radius * 2},0')` 
                  }}
              ></div>
              <div
                  className="absolute border-2 border-dashed border-cyan-400 rounded-full cursor-move"
                  style={{
                      left: cropParams.x - cropParams.radius,
                      top: cropParams.y - cropParams.radius,
                      width: cropParams.radius * 2,
                      height: cropParams.radius * 2,
                  }}
                  onMouseDown={handleDragStart}
                  onTouchStart={handleDragStart}
              ></div>
            </>
          )}
      </div>

      <div className={`p-4 bg-gray-900/80 backdrop-blur-sm flex-shrink-0 transition-opacity duration-300 ${status === 'editing' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
          <div className="flex flex-col space-y-2">
            <div className="flex justify-between items-baseline px-2">
              <label className="text-sm font-medium text-gray-300" id="crop-size-label">{t('cropSize')}</label>
              <span className="text-sm font-mono text-cyan-400">{Math.round(cropParams.radius)}</span>
            </div>
            <div className="flex items-center justify-center space-x-4" role="group" aria-labelledby="crop-size-label">
                <button 
                  onClick={() => handleRadiusChange(cropParams.radius - 5)} 
                  className="bg-gray-700 hover:bg-gray-600 text-white font-bold text-2xl w-16 h-12 rounded-full transition-colors flex items-center justify-center active:bg-gray-500"
                  aria-label={t('decreaseCrop')}
                >
                  -
                </button>
                <button 
                  onClick={() => handleRadiusChange(cropParams.radius + 5)}
                  className="bg-gray-700 hover:bg-gray-600 text-white font-bold text-2xl w-16 h-12 rounded-full transition-colors flex items-center justify-center active:bg-gray-500"
                  aria-label={t('increaseCrop')}
                >
                  +
                </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-6">
              <button onClick={onRetake} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-full transition-colors">
                  {t('retake')}
              </button>
              <button onClick={handleContinue} className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-3 px-4 rounded-full transition-colors">
                  {t('continue')}
              </button>
          </div>
      </div>
    </div>
  );
};

export default CropScreen;