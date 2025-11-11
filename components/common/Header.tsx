
import React from 'react';
import { SparklesIcon } from './Icons';
import { useLocalization } from '../../lib/localization';

interface HeaderProps {
    credits: number;
}

const Header: React.FC<HeaderProps> = ({ credits }) => {
  const { t } = useLocalization();
  return (
    <header className="flex-shrink-0 bg-black/50 backdrop-blur-sm p-4 flex justify-between items-center z-50">
      <h1 className="text-xl font-bold text-white">SnapEyes</h1>
      <div className="flex items-center space-x-2 bg-gray-800 px-3 py-1 rounded-full">
        <SparklesIcon className="w-5 h-5 text-cyan-400" />
        <span className="font-bold text-white">{credits}</span>
        <span className="text-sm text-gray-400">{t('credits')}</span>
      </div>
    </header>
  );
};

export default Header;