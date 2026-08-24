import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const LanguageDropdown: React.FC = () => {
  const { currentLanguage, setLanguage } = useLanguage();

  const languages = [
    { code: 'en', label: 'EN' },
    { code: 'hi', label: 'HI' },
  ];

  return (
    <div className="flex items-center gap-1 p-0.5 rounded-xl bg-iosGray-100 dark:bg-iosGray-800">
      {languages.map(({ code, label }) => (
        <button
          key={code}
          type="button"
          onClick={() => setLanguage(code)}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-sf transition-colors ${
            currentLanguage === code
              ? 'bg-iosBlue-500 text-white shadow-sm'
              : 'text-iosGray-600 dark:text-iosGray-400 hover:text-iosGray-900 dark:hover:text-white'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
};

export default LanguageDropdown;
