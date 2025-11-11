
import React from 'react';
import { AppScreen } from '../../types';
import { CameraIcon, CollectionIcon, CogIcon, ShoppingCartIcon, IridologyIcon } from './Icons';
import { useLocalization } from '../../lib/localization';

interface BottomNavProps {
  activeTab: AppScreen;
  setActiveTab: (tab: AppScreen) => void;
}

const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  const { t } = useLocalization();
  
  const navItems = [
    { screen: AppScreen.GALLERY, icon: <CollectionIcon className="w-7 h-7" />, label: t('gallery') },
    { screen: AppScreen.IRIDOLOGY, icon: <IridologyIcon className="w-7 h-7" />, label: t('iridology') },
    { screen: AppScreen.CAPTURE, icon: <CameraIcon className="w-8 h-8" />, label: t('capture') },
    { screen: AppScreen.STORE, icon: <ShoppingCartIcon className="w-7 h-7" />, label: t('store') },
    { screen: AppScreen.SETTINGS, icon: <CogIcon className="w-7 h-7" />, label: t('settings') },
  ];

  return (
    <nav className="flex-shrink-0 bg-gray-900/80 backdrop-blur-sm flex justify-around items-center p-2 z-50">
      {navItems.map((item) => (
        <button
          key={item.screen}
          onClick={() => setActiveTab(item.screen)}
          className={`flex flex-col items-center justify-center p-2 rounded-lg transition-colors w-20 ${
            activeTab === item.screen ? 'text-cyan-400' : 'text-gray-400 hover:text-white'
          }`}
        >
          {item.label === t('capture') ? (
             <div className={`p-4 rounded-full -mt-8 mb-1 transition-all duration-200 ${activeTab === item.screen ? 'bg-cyan-500 shadow-lg shadow-cyan-500/30' : 'bg-gray-600'}`}>
                <CameraIcon className="w-8 h-8 text-black" />
             </div>
          ) : (
             <>
                {item.icon}
                <span className="text-xs mt-1">{item.label}</span>
             </>
          )}
        </button>
      ))}
    </nav>
  );
};

export default BottomNav;