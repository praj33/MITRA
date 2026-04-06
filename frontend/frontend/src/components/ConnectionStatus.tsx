import React, { useState, useEffect } from 'react';

const ConnectionStatus: React.FC = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Show "back online" message briefly
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 3000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowMessage(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check initial state
    if (!navigator.onLine) {
      setShowMessage(true);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!showMessage) return null;

  return (
    <div 
      className="fixed top-16 left-1/2 transform -translate-x-1/2 z-50 animate-slideDown"
      role="status"
      aria-live="polite"
    >
      <div 
        className={`
          backdrop-blur-xl text-white px-5 py-3 rounded-2xl shadow-ios-lg border border-white/20 
          flex items-center gap-3 min-w-[280px]
          ${isOnline ? 'bg-green-500/95 dark:bg-green-600/95' : 'bg-orange-500/95 dark:bg-orange-600/95'}
        `}
      >
        {isOnline ? (
          <>
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <div>
              <p className="text-sm font-semibold font-sf">You're back online</p>
            </div>
          </>
        ) : (
          <>
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
            </svg>
            <div>
              <p className="text-sm font-semibold font-sf">You're offline</p>
              <p className="text-xs font-sf opacity-90">Check your internet connection</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ConnectionStatus;
