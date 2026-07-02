// components/primitives/Badge.tsx
import React from 'react';
import { cn } from '../../lib/utils';

type Variant = 'default' | 'brand' | 'success' | 'warning' | 'error' | 'info';

interface Props {
  variant?: Variant;
  size?: 'sm' | 'md';
  dot?: boolean;
  children: React.ReactNode;
  className?: string;
}

const variants: Record<Variant, string> = {
  default: 'bg-surface-overlay text-text-secondary border-border-subtle',
  brand:   'bg-brand-muted text-brand-light border-brand/30',
  success: 'bg-state-success/10 text-state-success border-state-success/20',
  warning: 'bg-state-warning/10 text-state-warning border-state-warning/20',
  error:   'bg-state-error/10 text-state-error border-state-error/20',
  info:    'bg-state-info/10 text-state-info border-state-info/20',
};

const Badge: React.FC<Props> = ({
  variant = 'default', size = 'sm', dot, children, className,
}) => (
  <span className={cn(
    'inline-flex items-center gap-1 border rounded-full font-medium',
    size === 'sm' ? 'px-2 py-0.5 text-2xs' : 'px-2.5 py-1 text-xs',
    variants[variant],
    className,
  )}>
    {dot && (
      <span className={cn('w-1 h-1 rounded-full', {
        'bg-text-secondary': variant === 'default',
        'bg-brand':          variant === 'brand',
        'bg-state-success':  variant === 'success',
        'bg-state-warning':  variant === 'warning',
        'bg-state-error':    variant === 'error',
        'bg-state-info':     variant === 'info',
      })} />
    )}
    {children}
  </span>
);

export default Badge;
