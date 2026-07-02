// components/cards/KPICard.tsx — Quick metric display
import React from 'react';
import { cn } from '../../lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Props {
  label:    string;
  value:    string | number;
  unit?:    string;
  trend?:   'up' | 'down' | 'flat';
  trendLabel?: string;
  accent?:  'brand' | 'success' | 'warning' | 'error' | 'default';
  className?: string;
}

const accentColor = {
  brand:   'text-brand-light',
  success: 'text-state-success',
  warning: 'text-state-warning',
  error:   'text-state-error',
  default: 'text-text-primary',
};

const KPICard: React.FC<Props> = ({
  label, value, unit, trend, trendLabel, accent = 'default', className,
}) => (
  <div className={cn('card p-3.5', className)}>
    <p className="text-2xs font-medium text-text-muted uppercase tracking-wider mb-1.5">
      {label}
    </p>
    <div className="flex items-baseline gap-1">
      <span className={cn('text-2xl font-bold', accentColor[accent])}>
        {value}
      </span>
      {unit && <span className="text-xs text-text-muted">{unit}</span>}
    </div>
    {trend && (
      <div className={cn(
        'flex items-center gap-1 mt-1.5 text-2xs',
        trend === 'up'   ? 'text-state-success' :
        trend === 'down' ? 'text-state-error' :
        'text-text-muted',
      )}>
        {trend === 'up'   && <TrendingUp  size={10} />}
        {trend === 'down' && <TrendingDown size={10} />}
        {trend === 'flat' && <Minus        size={10} />}
        {trendLabel && <span>{trendLabel}</span>}
      </div>
    )}
  </div>
);

export default KPICard;
