// components/cards/StatusCard.tsx — System / capability status
import React from 'react';
import { cn } from '../../lib/utils';
import { CheckCircle, AlertCircle, AlertTriangle, Activity } from 'lucide-react';
import Badge from '../primitives/Badge';

interface StatusItem {
  name:   string;
  status: 'operational' | 'degraded' | 'unavailable';
}

interface Props {
  title?:  string;
  items:   StatusItem[];
  className?: string;
}

const statusConfig = {
  operational: { icon: <CheckCircle  size={11} className="text-state-success" />, variant: 'success' as const, label: 'OK' },
  degraded:    { icon: <AlertTriangle size={11} className="text-state-warning" />, variant: 'warning' as const, label: 'Degraded' },
  unavailable: { icon: <AlertCircle  size={11} className="text-state-error"   />, variant: 'error'   as const, label: 'Down' },
};

const StatusCard: React.FC<Props> = ({ title = 'System Status', items, className }) => {
  const allOk = items.every(i => i.status === 'operational');
  return (
    <div className={cn('card p-3.5', className)}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-2xs font-semibold text-text-muted uppercase tracking-wider">{title}</p>
        <div className="flex items-center gap-1.5">
          <Activity size={10} className={allOk ? 'text-state-success' : 'text-state-warning'} />
          <span className={cn('text-2xs font-medium', allOk ? 'text-state-success' : 'text-state-warning')}>
            {allOk ? 'All systems OK' : 'Issues detected'}
          </span>
        </div>
      </div>
      <div className="space-y-1.5">
        {items.map(item => {
          const cfg = statusConfig[item.status];
          return (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                {cfg.icon}
                <span className="text-xs text-text-secondary">{item.name}</span>
              </div>
              <Badge variant={cfg.variant} size="sm">{cfg.label}</Badge>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatusCard;
