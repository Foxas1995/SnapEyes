import React from 'react';
import { HistoryItem } from '../types';
import { useLocalization } from '../lib/localization';

interface GalleryScreenProps {
  history: HistoryItem[];
}

const GalleryScreen: React.FC<GalleryScreenProps> = ({ history }) => {
  const { t } = useLocalization();

  return (
    <div className="p-4 bg-gray-900 min-h-full">
      <h2 className="text-3xl font-bold text-center mb-6">{t('myGallery')}</h2>
      {history.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-4/5 text-center text-gray-500">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>{t('galleryEmpty')}</p>
          <p className="text-sm">{t('galleryEmptySub')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
          {history.map((item) => (
            <div key={item.id} className="aspect-square bg-gray-800 rounded-md overflow-hidden">
              <img 
                src={item.thumbnail} 
                alt="Saved SnapEyes photo"
                className="w-full h-full object-cover"
                onClick={() => alert('Re-editing coming soon!')}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GalleryScreen;