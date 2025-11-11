import React from 'react';
import { MailIcon, DocumentTextIcon, TrashIcon, InfoIcon } from './common/Icons';
import { useLocalization } from '../lib/localization';

const SettingsScreen: React.FC = () => {
  const { t, language, setLanguage } = useLocalization();
  
  return (
    <div className="p-6 bg-gray-900 min-h-full">
      <h2 className="text-3xl font-bold text-center mb-8">{t('settingsTitle')}</h2>
      
      <div className="space-y-4">
        <div>
          <h3 className="text-cyan-400 font-semibold mb-2 px-2">{t('language')}</h3>
          <div className="bg-gray-800 p-1 rounded-lg flex">
            <button 
              onClick={() => setLanguage('en')}
              className={`w-1/2 py-2 rounded-md font-semibold transition-colors ${language === 'en' ? 'bg-cyan-500 text-black' : 'text-white'}`}
            >
              English
            </button>
            <button 
              onClick={() => setLanguage('lt')}
              className={`w-1/2 py-2 rounded-md font-semibold transition-colors ${language === 'lt' ? 'bg-cyan-500 text-black' : 'text-white'}`}
            >
              Lietuvių
            </button>
          </div>
        </div>

        <div className="space-y-2 pt-4">
            <SettingsItem icon={<MailIcon className="w-6 h-6 text-cyan-400" />} label={t('contactSupport')} onClick={() => window.location.href = 'mailto:support@snapeyes.app'} />
            <SettingsItem icon={<DocumentTextIcon className="w-6 h-6 text-cyan-400" />} label={t('privacyPolicy')} onClick={() => alert('Link to privacy policy would go here.')} />
            <SettingsItem icon={<TrashIcon className="w-6 h-6 text-red-400" />} label={t('deleteData')} onClick={() => alert('A request would be sent to delete your data.')} />
            <SettingsItem icon={<InfoIcon className="w-6 h-6 text-cyan-400" />} label={t('termsAbout')} onClick={() => alert('App Version 1.0.0')} />
        </div>
      </div>

      <div className="absolute bottom-16 left-0 right-0 text-center text-gray-600 text-sm">
        <p>{t('appVersion')} 1.0.0</p>
        <p>support@snapeyes.app</p>
      </div>
    </div>
  );
};

const SettingsItem: React.FC<{icon: React.ReactNode, label: string, onClick: () => void}> = ({ icon, label, onClick }) => (
  <button onClick={onClick} className="w-full bg-gray-800 hover:bg-gray-700 p-4 rounded-lg flex items-center space-x-4 text-left transition-colors">
    {icon}
    <span className="flex-grow">{label}</span>
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  </button>
);

export default SettingsScreen;