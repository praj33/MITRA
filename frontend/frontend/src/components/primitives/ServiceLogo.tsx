import React from 'react';
import { cn } from '../../lib/utils';

export type ServiceProvider =
  | 'google'
  | 'microsoft'
  | 'github'
  | 'apple'
  | 'whatsapp'
  | 'apple_calendar'
  | 'calendar';

export interface ServiceLogoProps {
  service: ServiceProvider | string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeConfig = {
  sm: {
    container: 'w-9 h-9 min-w-[36px] rounded-xl',
    icon: 'w-4 h-4',
  },
  md: {
    container: 'w-11 h-11 sm:w-12 sm:h-12 min-w-[44px] rounded-2xl',
    icon: 'w-5 h-5 sm:w-6 sm:h-6',
  },
  lg: {
    container: 'w-13 h-13 sm:w-14 sm:h-14 min-w-[52px] rounded-2xl',
    icon: 'w-7 h-7',
  },
};

export const ServiceLogo: React.FC<ServiceLogoProps> = ({
  service,
  size = 'md',
  className,
}) => {
  const norm = (service || '').toLowerCase().trim();
  const conf = sizeConfig[size] || sizeConfig.md;

  const renderIcon = () => {
    switch (norm) {
      case 'google':
        return (
          <svg className={conf.icon} viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
        );

      case 'microsoft':
      case 'outlook':
        return (
          <svg className={conf.icon} viewBox="0 0 24 24" aria-hidden="true">
            <rect x="2" y="2" width="9.5" height="9.5" rx="1.5" fill="#F25022" />
            <rect x="12.5" y="2" width="9.5" height="9.5" rx="1.5" fill="#7FBA00" />
            <rect x="2" y="12.5" width="9.5" height="9.5" rx="1.5" fill="#00A4EF" />
            <rect x="12.5" y="12.5" width="9.5" height="9.5" rx="1.5" fill="#FFB900" />
          </svg>
        );

      case 'github':
        return (
          <svg className={cn(conf.icon, "fill-current text-text-primary")} viewBox="0 0 24 24" aria-hidden="true">
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
            />
          </svg>
        );

      case 'apple':
        return (
          <svg className={cn(conf.icon, "fill-current text-text-primary")} viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.85c.66-.8 1.11-1.92.99-3.04-.96.04-2.12.64-2.8 1.44-.61.71-1.14 1.86-1 2.97 1.07.08 2.15-.57 2.81-1.37z" />
          </svg>
        );

      case 'whatsapp':
        return (
          <svg className={cn(conf.icon, "fill-[#25D366]")} viewBox="0 0 24 24" aria-hidden="true">
            <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-1.099 4.019 4.012-1.052z" />
          </svg>
        );

      case 'apple_calendar':
      case 'calendar':
      default:
        return (
          <svg className={conf.icon} viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <rect x="3" y="4" width="18" height="17" rx="3.5" fill="#1C1C24" stroke="rgba(255,255,255,0.2)" strokeWidth="1.2" />
            <path d="M3 8.5C3 6.567 4.567 5 6.5 5H17.5C19.433 5 21 6.567 21 8.5V9H3V8.5Z" fill="#FF3B30" />
            <circle cx="8" cy="3" r="1.2" fill="#FFFFFF" />
            <circle cx="16" cy="3" r="1.2" fill="#FFFFFF" />
            <rect x="7" y="12" width="2.5" height="2.5" rx="0.6" fill="#FFFFFF" fillOpacity="0.85" />
            <rect x="11" y="12" width="2.5" height="2.5" rx="0.6" fill="#FFFFFF" fillOpacity="0.85" />
            <rect x="15" y="12" width="2.5" height="2.5" rx="0.6" fill="#FFFFFF" fillOpacity="0.85" />
            <rect x="7" y="16" width="2.5" height="2.5" rx="0.6" fill="#FFFFFF" fillOpacity="0.6" />
            <rect x="11" y="16" width="2.5" height="2.5" rx="0.6" fill="#FFFFFF" fillOpacity="0.6" />
            <rect x="15" y="16" width="2.5" height="2.5" rx="0.6" fill="#FF3B30" />
          </svg>
        );
    }
  };

  return (
    <div
      className={cn(
        conf.container,
        'bg-surface-elevated/90 border border-border-subtle flex items-center justify-center flex-shrink-0 shadow-sm transition-transform duration-150',
        className,
      )}
    >
      {renderIcon()}
    </div>
  );
};

export default ServiceLogo;
