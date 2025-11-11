import React from 'react';
import { CameraIcon, SparklesIcon, EyeIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';

interface OnboardingScreenProps {
  onComplete: () => void;
}

const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
  const { t, language, setLanguage } = useLocalization();

  return (
    <div className="flex flex-col min-h-full justify-between items-center text-center p-8 bg-gray-900">
      <div className="w-full flex justify-center mt-4">
        <div className="bg-gray-800 p-1 rounded-full flex space-x-1">
          <button
            onClick={() => setLanguage('en')}
            className={`px-4 py-1 rounded-full text-sm font-semibold ${language === 'en' ? 'bg-cyan-500 text-black' : 'text-white'}`}
          >
            English
          </button>
          <button
            onClick={() => setLanguage('lt')}
            className={`px-4 py-1 rounded-full text-sm font-semibold ${language === 'lt' ? 'bg-cyan-500 text-black' : 'text-white'}`}
          >
            Lietuvių
          </button>
        </div>
      </div>

      <div className="mt-8">
        <EyeIcon className="w-24 h-24 mx-auto text-cyan-400" />
        <h1 className="text-4xl font-bold mt-4">{t('onboardingTitle')}</h1>
        <p className="text-lg text-gray-300 mt-2">{t('onboardingSubtitle')}</p>
      </div>

      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <CameraIcon className="w-10 h-10 text-cyan-400 flex-shrink-0" />
          <p className="text-left text-gray-200">{t('onboardingFeature1')}</p>
        </div>
        <div className="flex items-center space-x-4">
          <SparklesIcon className="w-10 h-10 text-cyan-400 flex-shrink-0" />
          <p className="text-left text-gray-200">{t('onboardingFeature2')}</p>
        </div>
        <div className="flex items-center space-x-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-cyan-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.022 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
          </svg>
          <p className="text-left text-gray-200">{t('onboardingFeature3')}</p>
        </div>
      </div>

      <div className="w-full">
         <p className="text-xs text-gray-500 mb-4">{t('onboardingPrivacy')}</p>
        <button
          onClick={onComplete}
          className="w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold py-4 px-4 rounded-full transition-transform duration-200 ease-in-out transform hover:scale-105"
        >
          {t('getStarted')}
        </button>
      </div>
    </div>
  );
};

export default OnboardingScreen;