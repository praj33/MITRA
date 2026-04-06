import React, { createContext, useContext, useState, useCallback } from 'react';

interface LanguageContextType {
  currentLanguage: string;
  setLanguage: (lang: string) => void;
  isRTL: boolean;
}

const LanguageContext = createContext<LanguageContextType>({
  currentLanguage: 'en',
  setLanguage: () => {},
  isRTL: false,
});

// Map of RTL languages
const RTL_LANGUAGES = ['ar', 'he', 'ur', 'fa'];

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState('en');

  const setLanguage = useCallback((lang: string) => {
    setCurrentLanguage(lang);
  }, []);

  const isRTL = RTL_LANGUAGES.includes(currentLanguage);

  return (
    <LanguageContext.Provider value={{ currentLanguage, setLanguage, isRTL }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
