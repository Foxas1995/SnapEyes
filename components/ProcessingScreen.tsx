
import React, { useEffect, useRef, useState } from 'react';
import { enhanceEyeImage } from '../services/geminiService';
import { EyeIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';
import { CropData } from '../types';

interface ProcessingScreenProps {
  originalImage: string;
  cropData: CropData;
  onComplete: (composedBeforeDataUrl: string, enhancedImageDataUrl:string) => void;
  onError: () => void;
}

// This function creates a tight, square crop of the iris.
// It's used as input for the enhancement AI.
const cropImage = (originalImageSrc: string, irisData: CropData): Promise<string> => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            
            const sourceX = (irisData.centerX * img.naturalWidth) - (irisData.radius * img.naturalWidth);
            const sourceY = (irisData.centerY * img.naturalHeight) - (irisData.radius * img.naturalWidth);
            const size = (irisData.radius * img.naturalWidth) * 2;

            canvas.width = 512;
            canvas.height = 512;
            const ctx = canvas.getContext('2d');
            
            if (ctx) {
                ctx.drawImage(img, sourceX, sourceY, size, size, 0, 0, 512, 512);
                const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
                resolve(dataUrl);
            } else {
                reject(new Error('Canvas 2D context not available'));
            }
        };
        img.onerror = () => reject(new Error('Could not load image for cropping'));
        img.src = originalImageSrc;
    });
};


// This function creates a "before" image for the comparison slider.
// It centers the un-enhanced iris on a black background to match the composition of the enhanced "after" image.
const createComposedBeforeImage = (originalImageSrc: string, irisData: CropData): Promise<string> => {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 512;
            canvas.height = 512;
            const ctx = canvas.getContext('2d');
            if (!ctx) return reject(new Error('Canvas context not available'));
            
            // Fill background with black
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Scale the iris to fill about 90% of the canvas, matching the enhanced image's composition.
            const scale = 0.9;
            const destDiameter = canvas.width * scale;
            const destRadius = destDiameter / 2;

            // Define the source region from the original image
            const sourceRadius = irisData.radius * img.naturalWidth;
            const sourceDiameter = sourceRadius * 2;
            const sourceX = (irisData.centerX * img.naturalWidth) - sourceRadius;
            const sourceY = (irisData.centerY * img.naturalHeight) - sourceRadius;

            // Create a circular clipping path in the center of the destination canvas
            ctx.save();
            ctx.beginPath();
            ctx.arc(canvas.width / 2, canvas.height / 2, destRadius, 0, Math.PI * 2, true);
            ctx.clip();

            // Draw the source iris region into the clipped circle
            ctx.drawImage(
                img, 
                sourceX, 
                sourceY, 
                sourceDiameter, 
                sourceDiameter, 
                (canvas.width - destDiameter) / 2, 
                (canvas.height - destDiameter) / 2, 
                destDiameter, 
                destDiameter
            );
            
            ctx.restore();

            resolve(canvas.toDataURL('image/jpeg', 0.95));
        };
        img.onerror = () => reject(new Error('Could not load image for composing'));
        img.src = originalImageSrc;
    });
};


const ProcessingScreen: React.FC<ProcessingScreenProps> = ({ originalImage, cropData, onComplete, onError }) => {
  const hasProcessed = useRef(false);
  const { t } = useLocalization();
  const [statusText, setStatusText] = useState(t('enhancing'));

  useEffect(() => {
    if (hasProcessed.current || !cropData) return;
    hasProcessed.current = true;

    const processImage = async () => {
      try {
        const irisData = cropData;

        // Add a compositional safety margin to prevent clipping the edge of the iris.
        const safeIrisData = {
            ...irisData,
            radius: irisData.radius * 0.95, // Use 95% of the detected radius.
        };

        // Step 1: Create a tight crop for the AI model using the safe detected data
        setStatusText(t('enhancing'));
        const tightCropDataUrl = await cropImage(originalImage, safeIrisData);
        
        // Step 2: Enhance the tight crop with the AI
        const tightCropBase64Data = tightCropDataUrl.split(',')[1];
        const enhancedBase64 = await enhanceEyeImage(tightCropBase64Data);
        
        // Step 3: Create a composed "before" image using the safe data for a smooth comparison slider
        const composedBeforeDataUrl = await createComposedBeforeImage(originalImage, safeIrisData);

        onComplete(composedBeforeDataUrl, `data:image/png;base64,${enhancedBase64}`);
      } catch (error) {
        console.error("Processing failed:", error);
        onError();
      }
    };

    processImage();
  }, [originalImage, cropData, onComplete, onError, t]);

  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-gray-900">
      <div className="relative">
        <EyeIcon className="w-48 h-48 text-cyan-400 animate-pulse" />
        <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 border-2 border-cyan-500 rounded-full animate-spin-slow"></div>
        </div>
         <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-40 h-40 border-2 border-cyan-300 rounded-full animate-spin-slow-reverse"></div>
        </div>
      </div>
      <h2 className="text-2xl font-bold mt-12">{statusText}</h2>
      <p className="text-gray-300 mt-2">{statusText === t('locatingIris') ? t('locatingIrisSub') : t('enhancingSub')}</p>
      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 5s linear infinite;
        }
        @keyframes spin-slow-reverse {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }
        .animate-spin-slow-reverse {
            animation: spin-slow-reverse 6s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default ProcessingScreen;
