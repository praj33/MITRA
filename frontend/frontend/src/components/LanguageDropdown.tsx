import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const LANGUAGES: { code: string; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'zh-CN', label: '中文' },
  { code: 'ja', label: '日本語' },
  { code: 'ar', label: 'العربية' },
  { code: 'pt', label: 'Português' },
  { code: 'ru', label: 'Русский' },
  { code: 'it', label: 'Italiano' },
  { code: 'ko', label: '한국어' },
  { code: 'nl', label: 'Nederlands' },
  { code: 'tr', label: 'Türkçe' },
];

declare global {
  interface Window {
    google?: { 
      translate: { 
        TranslateElement: new (opts: { 
          pageLanguage: string; 
          includedLanguages?: string; 
          layout?: number;
        }, id: string) => void;
        InlineLayout?: { SIMPLE: number };
      };
    };
    googleTranslateElementInit?: () => void;
    __googleTranslateInitialized?: boolean;
  }
}

const LanguageDropdown: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [, setReady] = useState(false);
  const [selectedLang, setSelectedLang] = useState('en');
  const [isInitializing, setIsInitializing] = useState(false);
  const { setLanguage } = useLanguage();

  // Initialize Google Translate Widget
  useEffect(() => {
    // Prevent multiple initializations
    if (window.__googleTranslateInitialized || document.getElementById('google_translate_element')) {
      setReady(true);
      return;
    }

    setIsInitializing(true);

    // Create hidden container for Google Translate
    const container = document.createElement('div');
    container.id = 'google_translate_element';
    container.style.cssText = 'position: absolute; left: -9999px; top: -9999px; height: 0; overflow: hidden;';
    document.body.appendChild(container);

    // Add custom styles to hide Google branding while keeping functionality
    const style = document.createElement('style');
    style.textContent = `
      .goog-te-banner-frame { display: none !important; }
      .goog-logo-link { display: none !important; }
      .goog-te-gadget { height: 0 !important; overflow: hidden !important; }
      .goog-te-gadget > div { display: block !important; }
      body { top: 0 !important; position: static !important; }
      .skiptranslate { display: none !important; visibility: hidden !important; }
      iframe.skiptranslate { display: none !important; }
      #goog-gt-tt { display: none !important; }
      /* Hide the widget but keep the select element functional */
      .goog-te-menu-frame { display: none !important; }
    `;
    document.head.appendChild(style);

    // Define the initialization callback
    window.googleTranslateElementInit = () => {
      if (window.google?.translate?.TranslateElement) {
        try {
          const langCodes = LANGUAGES.map(l => l.code).join(',');
          
          new window.google.translate.TranslateElement(
            { 
              pageLanguage: 'en',
              includedLanguages: langCodes,
              layout: window.google.translate.InlineLayout?.SIMPLE || 0
            },
            'google_translate_element'
          );
          
          window.__googleTranslateInitialized = true;
          
          // Wait for the combo box to be created
          const checkInterval = setInterval(() => {
            const combo = document.querySelector('.goog-te-combo') as HTMLSelectElement;
            if (combo) {
              clearInterval(checkInterval);
              setReady(true);
              setIsInitializing(false);
            }
          }, 200);

          // Clear interval after 5 seconds max
          setTimeout(() => clearInterval(checkInterval), 5000);
          
        } catch (err) {
          console.error('Failed to initialize Google Translate:', err);
          setIsInitializing(false);
        }
      }
    };

    // Load Google Translate script
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.async = true;
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    
    script.onerror = () => {
      console.error('Failed to load Google Translate script');
      setIsInitializing(false);
    };
    
    document.body.appendChild(script);

    return () => {
      // Cleanup is handled by checking __googleTranslateInitialized flag
    };
  }, []);

  const selectLanguage = useCallback((code: string) => {
    const combo = document.querySelector('.goog-te-combo') as HTMLSelectElement;
    
    if (!combo) {
      console.warn('Google Translate widget not ready');
      return;
    }

    // Update language context for TTS
    setLanguage(code);

    if (code === 'en') {
      // Reset to English by clearing Google Translate cookie and reloading
      // The googtrans cookie stores the translation state
      document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + window.location.hostname;
      
      // Also try to reset via the combo box if possible
      if (combo && combo.value !== 'en') {
        combo.value = 'en';
        combo.dispatchEvent(new Event('change', { bubbles: true }));
      }
      
      // Reload to clear translation
      window.location.href = window.location.pathname;
      return;
    }

    // Change the language
    if (combo.value !== code) {
      combo.value = code;
      combo.dispatchEvent(new Event('change', { bubbles: true }));
      setSelectedLang(code);
    }
    
    setOpen(false);
  }, [setLanguage]);

  const currentLangLabel = LANGUAGES.find(l => l.code === selectedLang)?.label || 'Language';

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={isInitializing}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-iosGray-100 dark:bg-iosGray-800 text-iosGray-700 dark:text-iosGray-300 hover:bg-iosGray-200 dark:hover:bg-iosGray-700 transition-colors font-sf text-sm disabled:opacity-50"
        title={isInitializing ? "Loading translation..." : "Change language"}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
        </svg>
        <span className="hidden sm:inline">{isInitializing ? 'Loading...' : currentLangLabel}</span>
        <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {open && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            aria-hidden="true" 
            onClick={() => setOpen(false)} 
          />
          <div className="absolute right-0 top-full mt-1 z-50 py-1 w-48 max-h-64 overflow-y-auto rounded-xl bg-white dark:bg-iosGray-800 shadow-ios border border-iosGray-200/50 dark:border-iosGray-700/50 font-sf text-sm">
            {LANGUAGES.map(({ code, label }) => (
              <button
                key={code}
                type="button"
                onClick={() => selectLanguage(code)}
                className={`w-full text-left px-4 py-2.5 hover:bg-iosGray-100 dark:hover:bg-iosGray-700 transition-colors ${
                  selectedLang === code ? 'bg-iosBlue-100 dark:bg-iosBlue-900 text-iosBlue-700 dark:text-iosBlue-300' : 'text-iosGray-900 dark:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageDropdown;
