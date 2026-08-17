import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const LANGUAGES = [
  { code: 'en', label: 'EN', name: 'English' },
  { code: 'hi', label: 'HI', name: 'Hindi' },
  { code: 'es', label: 'ES', name: 'Spanish' },
  { code: 'fr', label: 'FR', name: 'French' },
  { code: 'de', label: 'DE', name: 'German' },
  { code: 'ja', label: 'JA', name: 'Japanese' },
  { code: 'ko', label: 'KO', name: 'Korean' },
  { code: 'zh', label: 'ZH', name: 'Chinese' },
  { code: 'ar', label: 'AR', name: 'Arabic' },
  { code: 'pt', label: 'PT', name: 'Portuguese' },
  { code: 'ru', label: 'RU', name: 'Russian' },
];

const LanguageDropdown: React.FC = () => {
  const { currentLanguage, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 p-0.5 rounded-xl bg-iosGray-100 dark:bg-iosGray-800 overflow-x-auto">
      {LANGUAGES.map(({ code, label, name }) => (
        <button
          key={code}
          type="button"
          onClick={() => setLanguage(code)}
          title={name}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-sf transition-colors whitespace-nowrap ${
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
