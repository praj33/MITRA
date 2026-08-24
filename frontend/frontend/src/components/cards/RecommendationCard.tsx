// components/cards/RecommendationCard.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, X, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Props {
  title:       string;
  description?: string;
  action?:     { label: string; onClick: () => void };
  onDismiss?:  () => void;
  className?:  string;
}

const RecommendationCard: React.FC<Props> = ({
  title, description, action, onDismiss, className,
}) => (
  <motion.div
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -4, height: 0 }}
    className={cn(
      'card card-brand p-3.5 relative group',
      className,
    )}
  >
    {onDismiss && (
      <button
        onClick={onDismiss}
        className="absolute top-3 right-3 text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X size={12} />
      </button>
    )}
    <div className="flex items-start gap-2.5">
      <div className="flex-shrink-0 w-6 h-6 rounded-md bg-brand-muted flex items-center justify-center">
        <Lightbulb size={12} className="text-brand-light" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-text-primary">{title}</p>
        {description && (
          <p className="text-2xs text-text-muted mt-0.5 leading-relaxed">{description}</p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-2 text-2xs font-medium text-brand-light hover:text-brand transition-colors flex items-center gap-1"
          >
            {action.label} <ArrowRight size={10} />
          </button>
        )}
      </div>
    </div>
  </motion.div>
);

export default RecommendationCard;
