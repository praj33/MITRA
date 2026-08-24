// components/cards/ContextCard.tsx — Right panel info cards
import React from 'react';
import { cn, formatRelative } from '../../lib/utils';
import { ContextItem } from '../../store/companion.store';
import { Calendar, Mail, CheckSquare, FileText, User, BookOpen } from 'lucide-react';

interface Props {
  item:      ContextItem;
  onAction?: (action: string, item: ContextItem) => void;
  className?: string;
}

const typeIcon: Record<ContextItem['type'], React.ReactNode> = {
  calendar: <Calendar  size={13} className="text-state-info" />,
  email:    <Mail      size={13} className="text-brand-light" />,
  task:     <CheckSquare size={13} className="text-state-success" />,
  note:     <FileText  size={13} className="text-state-warning" />,
  contact:  <User      size={13} className="text-text-secondary" />,
  knowledge:<BookOpen  size={13} className="text-brand-light" />,
};

const ContextCard: React.FC<Props> = ({ item, onAction, className }) => (
  <div className={cn(
    'flex items-start gap-2.5 p-3 rounded-lg bg-surface-overlay border border-border-subtle',
    'hover:border-border-default transition-all duration-150 cursor-default group',
    className,
  )}>
    <div className="flex-shrink-0 w-6 h-6 rounded-md bg-surface-elevated flex items-center justify-center mt-0.5">
      {typeIcon[item.type]}
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium text-text-primary truncate">{item.title}</p>
      {item.subtitle && (
        <p className="text-2xs text-text-muted truncate mt-0.5">{item.subtitle}</p>
      )}
      {item.value && (
        <p className="text-2xs text-text-secondary mt-1 truncate">{item.value}</p>
      )}
    </div>
    {item.timestamp && (
      <span className="text-2xs text-text-muted whitespace-nowrap flex-shrink-0">
        {formatRelative(item.timestamp)}
      </span>
    )}
  </div>
);

export default ContextCard;
