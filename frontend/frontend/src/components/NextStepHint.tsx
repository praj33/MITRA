import React from 'react';

interface NextStepHintProps {
  message: string;
  type?: 'info' | 'success' | 'suggestion';
}

const NextStepHint: React.FC<NextStepHintProps> = ({ message, type = 'info' }) => {
  const iconColors = {
    info: 'text-iosBlue-500',
    success: 'text-green-500',
    suggestion: 'text-purple-500',
  };

  const bgColors = {
    info: 'bg-iosBlue-50/80 dark:bg-iosBlue-900/20 backdrop-blur-md border-iosBlue-200/50 dark:border-iosBlue-800/30',
    success: 'bg-green-50/80 dark:bg-green-900/20 backdrop-blur-md border-green-200/50 dark:border-green-800/30',
    suggestion: 'bg-purple-50/80 dark:bg-purple-900/20 backdrop-blur-md border-purple-200/50 dark:border-purple-800/30',
  };

  const textColors = {
    info: 'text-iosBlue-700 dark:text-iosBlue-300',
    success: 'text-green-700 dark:text-green-300',
    suggestion: 'text-purple-700 dark:text-purple-300',
  };

  return (
    <div className={`mt-3 pt-3 border-t border-iosGray-200/50 dark:border-iosGray-700/50`}>
      <div className={`flex items-start gap-2 rounded-2xl px-4 py-2.5 ${bgColors[type]} border`}>
        <svg className={`w-4 h-4 ${iconColors[type]} mt-0.5 flex-shrink-0`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className={`text-xs ${textColors[type]} italic font-sf`}>
          {message}
        </p>
      </div>
    </div>
  );
};

export default NextStepHint;
