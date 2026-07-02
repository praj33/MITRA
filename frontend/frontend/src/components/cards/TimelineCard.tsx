// components/cards/TimelineCard.tsx — Workflow step progress
import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Circle, Loader, XCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface TimelineStep {
  id:          string;
  label:       string;
  description?: string;
  status:      'done' | 'active' | 'pending' | 'error';
}

interface Props {
  title:    string;
  steps:    TimelineStep[];
  className?: string;
}

const stepIcon = (status: TimelineStep['status']) => {
  if (status === 'done')    return <CheckCircle size={14} className="text-state-success" />;
  if (status === 'active')  return <Loader      size={14} className="text-brand animate-spin" />;
  if (status === 'error')   return <XCircle     size={14} className="text-state-error" />;
  return <Circle size={14} className="text-text-muted" />;
};

const TimelineCard: React.FC<Props> = ({ title, steps, className }) => (
  <div className={cn('card p-4', className)}>
    <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
      {title}
    </h3>
    <div className="space-y-0">
      {steps.map((step, i) => (
        <div key={step.id} className="flex gap-3">
          {/* Line + icon */}
          <div className="flex flex-col items-center">
            <motion.div
              initial={{ scale: 0.7 }}
              animate={{ scale: 1 }}
              transition={{ delay: i * 0.06 }}
            >
              {stepIcon(step.status)}
            </motion.div>
            {i < steps.length - 1 && (
              <div className={cn(
                'w-px flex-1 mt-1 mb-1',
                step.status === 'done' ? 'bg-state-success/30' : 'bg-border-subtle',
              )} style={{ minHeight: 16 }} />
            )}
          </div>
          {/* Content */}
          <div className={cn(
            'pb-3 min-w-0',
            i < steps.length - 1 && 'mb-0',
          )}>
            <p className={cn(
              'text-xs font-medium leading-none',
              step.status === 'done'   ? 'text-text-secondary' :
              step.status === 'active' ? 'text-text-primary' :
              step.status === 'error'  ? 'text-state-error' :
              'text-text-muted',
            )}>
              {step.label}
            </p>
            {step.description && step.status !== 'pending' && (
              <p className="text-2xs text-text-muted mt-0.5">{step.description}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default TimelineCard;
