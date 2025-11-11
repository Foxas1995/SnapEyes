import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { translations } from './translations';

export type Language = 'en' | 'lt';

interface LocalizationContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: keyof typeof translations.en) => string;
}

const LocalizationContext = createContext<LocalizationContextType | undefined>(undefined);

export const LocalizationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      // 1. Check for a user's explicit choice in local storage first.
      const savedLang = localStorage.getItem('snapeyes_lang');
      if (savedLang === 'lt' || savedLang === 'en') {
        return savedLang;
      }

      // 2. If no choice is saved, detect the browser language.
      const browserLang = navigator.language.toLowerCase();
      if (browserLang.startsWith('lt')) {
        return 'lt'; // Suggest Lithuanian if the browser is set to it.
      }
    } catch (e) {
      // If local storage or navigator access fails, fall back safely.
      console.warn('Could not access storage or navigator language.');
    }

    // 3. Default to English.
    return 'en';
  });

  useEffect(() => {
    try {
      localStorage.setItem('snapeyes_lang', language);
    } catch(e) {
      console.warn('Could not save language preference.');
    }
  }, [language]);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
  };

  const t = useCallback((key: keyof typeof translations.en): string => {
    const langDict = translations[language];
    const enDict = translations.en;
    return langDict[key] || enDict[key] || key;
  }, [language]);

  const value = { language, setLanguage, t };

  return (
    <LocalizationContext.Provider value={value}>
      {children}
    </LocalizationContext.Provider>
  );
};

export const useLocalization = (): LocalizationContextType => {
  const context = useContext(LocalizationContext);
  if (context === undefined) {
    throw new Error('useLocalization must be used within a LocalizationProvider');
  }
  return context;
};