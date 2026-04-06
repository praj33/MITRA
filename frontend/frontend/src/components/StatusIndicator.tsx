import React from 'react';

interface StatusIndicatorProps {
  status: 'executed' | 'pending' | 'failed' | 'processing' | 'completed' | 'success' | 'error' | string;
  label?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, label }) => {
  const getStatusConfig = () => {
    if (!status) return {
      color: 'bg-iosGray-500',
      bgColor: 'bg-iosGray-100/80 dark:bg-iosGray-800 backdrop-blur-md',
      textColor: 'text-iosGray-700 dark:text-iosGray-400',
      borderColor: 'border-iosGray-300/50 dark:border-iosGray-700',
      icon: '○',
      pulse: false,
    };
    switch (status.toLowerCase()) {
      case 'executed':
      case 'completed':
      case 'success':
        return {
          color: 'bg-green-500',
          bgColor: 'bg-green-50/80 dark:bg-green-900/30 backdrop-blur-md',
          textColor: 'text-green-700 dark:text-green-400',
          borderColor: 'border-green-200/50 dark:border-green-500/50',
          icon: '✓',
          pulse: false,
        };
      case 'executing':
      case 'processing':
        return {
          color: 'bg-iosBlue-500',
          bgColor: 'bg-iosBlue-50/80 dark:bg-iosBlue-900/30 backdrop-blur-md',
          textColor: 'text-iosBlue-700 dark:text-iosBlue-400',
          borderColor: 'border-iosBlue-200/50 dark:border-iosBlue-500/50',
          icon: '⟳',
          pulse: true,
        };
      case 'pending':
        return {
          color: 'bg-yellow-500',
          bgColor: 'bg-yellow-50/80 dark:bg-yellow-900/30 backdrop-blur-md',
          textColor: 'text-yellow-700 dark:text-yellow-400',
          borderColor: 'border-yellow-200/50 dark:border-yellow-500/50',
          icon: '⏳',
          pulse: true,
        };
      case 'skipped':
        return {
          color: 'bg-orange-500',
          bgColor: 'bg-orange-50/80 dark:bg-orange-900/30 backdrop-blur-md',
          textColor: 'text-orange-700 dark:text-orange-400',
          borderColor: 'border-orange-200/50 dark:border-orange-500/50',
          icon: '⊘',
          pulse: false,
        };
      case 'failed':
      case 'error':
        return {
          color: 'bg-red-500',
          bgColor: 'bg-red-50/80 dark:bg-red-900/30 backdrop-blur-md',
          textColor: 'text-red-700 dark:text-red-400',
          borderColor: 'border-red-200/50 dark:border-red-500/50',
          icon: '✗',
          pulse: false,
        };
      default:
        return {
          color: 'bg-iosGray-500',
          bgColor: 'bg-iosGray-100/80 dark:bg-iosGray-800 backdrop-blur-md',
          textColor: 'text-iosGray-700 dark:text-iosGray-400',
          borderColor: 'border-iosGray-300/50 dark:border-iosGray-700',
          icon: '○',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();
  const displayLabel = label || status;

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl ${config.bgColor} ${config.borderColor} border text-xs font-semibold ${config.textColor} shadow-ios font-sf`}
    >
      <span className={`w-2 h-2 rounded-full ${config.color} ${config.pulse ? 'animate-pulse' : ''}`}></span>
      <span className="text-xs font-bold">{config.icon}</span>
      <span className="uppercase tracking-wide">{displayLabel}</span>
    </div>
  );
};

export default StatusIndicator;
