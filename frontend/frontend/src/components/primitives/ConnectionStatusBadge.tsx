import React from 'react';
import { CheckCircle2, AlertTriangle, RefreshCw, XCircle, Ban, Circle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type ServiceStatusType =
  | 'CONNECTED'
  | 'NOT_CONNECTED'
  | 'NEEDS_REAUTH'
  | 'UNAVAILABLE'
  | 'SYNCING'
  | 'ERROR';

export interface ConnectionStatusBadgeProps {
  status: ServiceStatusType | string;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const ConnectionStatusBadge: React.FC<ConnectionStatusBadgeProps> = ({
  status,
  label,
  size = 'md',
  className,
}) => {
  const norm = (status || '').toUpperCase().trim();

  let resolvedStatus: ServiceStatusType = 'NOT_CONNECTED';
  if (norm === 'CONNECTED' || norm === 'ACTIVE') resolvedStatus = 'CONNECTED';
  else if (norm === 'NEEDS_REAUTH' || norm === 'NEEDS_REAUTHORIZATION') resolvedStatus = 'NEEDS_REAUTH';
  else if (norm === 'UNAVAILABLE' || norm === 'DISABLED') resolvedStatus = 'UNAVAILABLE';
  else if (norm === 'SYNCING') resolvedStatus = 'SYNCING';
  else if (norm === 'ERROR' || norm === 'FAILED') resolvedStatus = 'ERROR';

  const sizeClasses = size === 'sm'
    ? 'px-2 py-0.5 text-3xs gap-1 whitespace-nowrap'
    : 'px-2.5 py-1 text-2xs gap-1.5 whitespace-nowrap';

  const iconSize = size === 'sm' ? 10 : 12;

  switch (resolvedStatus) {
    case 'CONNECTED':
      return (
        <span
          className={cn(
            'inline-flex items-center font-semibold rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 select-none shadow-xs',
            sizeClasses,
            className,
          )}
        >
          <CheckCircle2 size={iconSize} className="text-emerald-400 flex-shrink-0" />
          <span>{label || 'Connected'}</span>
        </span>
      );

    case 'NEEDS_REAUTH':
      return (
        <span
          className={cn(
            'inline-flex items-center font-semibold rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 select-none shadow-xs',
            sizeClasses,
            className,
          )}
        >
          <AlertTriangle size={iconSize} className="text-amber-400 flex-shrink-0" />
          <span>{label || 'Needs Reauthorization'}</span>
        </span>
      );

    case 'SYNCING':
      return (
        <span
          className={cn(
            'inline-flex items-center font-semibold rounded-full bg-brand/15 border border-brand/30 text-brand-light select-none shadow-xs',
            sizeClasses,
            className,
          )}
        >
          <RefreshCw size={iconSize} className="text-brand-light animate-spin flex-shrink-0" />
          <span>{label || 'Syncing...'}</span>
        </span>
      );

    case 'ERROR':
      return (
        <span
          className={cn(
            'inline-flex items-center font-semibold rounded-full bg-red-500/10 border border-red-500/30 text-red-400 select-none shadow-xs',
            sizeClasses,
            className,
          )}
        >
          <XCircle size={iconSize} className="text-red-400 flex-shrink-0" />
          <span>{label || 'Sync Error'}</span>
        </span>
      );

    case 'UNAVAILABLE':
      return (
        <span
          className={cn(
            'inline-flex items-center font-medium rounded-full bg-surface-overlay/80 border border-border-subtle text-text-muted select-none',
            sizeClasses,
            className,
          )}
        >
          <Ban size={iconSize} className="text-text-muted flex-shrink-0" />
          <span>{label || 'Unavailable via Web'}</span>
        </span>
      );

    case 'NOT_CONNECTED':
    default:
      return (
        <span
          className={cn(
            'inline-flex items-center font-medium rounded-full bg-surface-overlay/60 border border-border-subtle text-text-muted select-none',
            sizeClasses,
            className,
          )}
        >
          <Circle size={iconSize} className="text-text-muted opacity-60 flex-shrink-0" />
          <span>{label || 'Not Connected'}</span>
        </span>
      );
  }
};

export default ConnectionStatusBadge;
