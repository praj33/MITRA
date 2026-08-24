// components/cards/SystemCard.tsx — Knowledge / UniGuru response
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Props {
  query:     string;
  answer:    string;
  source?:   string;
  followups?: string[];
  onFollowup?: (q: string) => void;
  className?: string;
}

const SystemCard: React.FC<Props> = ({
  query, answer, source, followups = [], onFollowup, className,
}) => {
  const [expanded, setExpanded] = useState(false);
  const preview = answer.slice(0, 180);
  const hasMore = answer.length > 180;

  return (
    <div className={cn('card card-info p-4', className)}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2.5">
        <div className="w-6 h-6 rounded-md bg-state-info/10 flex items-center justify-center">
          <BookOpen size={12} className="text-state-info" />
        </div>
        <span className="text-2xs font-semibold text-state-info uppercase tracking-wider">
          Knowledge
        </span>
        {source && (
          <span className="text-2xs text-text-muted ml-auto">via {source}</span>
        )}
      </div>

      {/* Query echo */}
      <p className="text-2xs text-text-muted mb-2 italic">"{query}"</p>

      {/* Answer */}
      <div className="text-sm text-text-primary leading-relaxed">
        <AnimatePresence mode="wait">
          {expanded ? (
            <motion.p key="full" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              {answer}
            </motion.p>
          ) : (
            <motion.p key="preview" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              {hasMore ? preview + '…' : answer}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-2xs text-brand-light hover:text-brand flex items-center gap-1 transition-colors"
        >
          {expanded ? <><ChevronUp size={10} /> Show less</> : <><ChevronDown size={10} /> Read more</>}
        </button>
      )}

      {/* Follow-ups */}
      {followups.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border-subtle">
          <p className="text-2xs text-text-muted mb-1.5">Explore further:</p>
          <div className="flex flex-col gap-1">
            {followups.slice(0, 3).map((q, i) => (
              <button
                key={i}
                onClick={() => onFollowup?.(q)}
                className="text-left text-xs text-text-secondary hover:text-brand-light transition-colors flex items-center gap-1 group"
              >
                <ArrowRight size={10} className="text-text-muted group-hover:text-brand-light flex-shrink-0" />
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemCard;
