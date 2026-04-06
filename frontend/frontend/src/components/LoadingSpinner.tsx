import React from 'react';

interface LoadingSpinnerProps {
  stage?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ stage }) => {
  const stages = [
    { name: 'Reading your message...', active: !stage || stage === 'input' },
    { name: 'Reviewing content...', active: stage === 'enforcement' },
    { name: 'Double-checking...', active: stage === 'safety' },
    { name: 'Understanding what you need...', active: stage === 'intent' },
    { name: 'Working on it...', active: stage === 'execution' },
  ];

  const currentStageIndex = stages.findIndex(s => s.active);
  const displayStage = stages[currentStageIndex]?.name || 'Processing...';

  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        <div className="w-5 h-5 border-2 border-iosBlue-400 dark:border-iosBlue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <div className="text-left">
        <div className="text-iosGray-700 dark:text-iosGray-300 text-sm font-sf">Thinking...</div>
        <div className="text-iosBlue-500 dark:text-iosBlue-400 text-xs font-sf">{displayStage}</div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
