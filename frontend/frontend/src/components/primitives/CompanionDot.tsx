// components/primitives/CompanionDot.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { CompanionStatus } from '../../store/companion.store';

interface Props {
  status: CompanionStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = { sm: 'w-1.5 h-1.5', md: 'w-2 h-2', lg: 'w-2.5 h-2.5' };

const CompanionDot: React.FC<Props> = ({ status, size = 'md', className }) => (
  <span
    role="status"
    aria-label={`Mitra is ${status}`}
    className={cn(
      'rounded-full flex-shrink-0 transition-all duration-300',
      sizes[size],
      status === 'active'   && 'dot-active',
      status === 'thinking' && 'dot-thinking',
      status === 'away'     && 'dot-away',
      status === 'error'    && 'dot-error',
      className,
    )}
  />
);

export default CompanionDot;
