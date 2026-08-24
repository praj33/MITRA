// components/primitives/Kbd.tsx
import React from 'react';
import { cn } from '../../lib/utils';

interface Props { keys: string[]; className?: string; }

const Kbd: React.FC<Props> = ({ keys, className }) => (
  <span className={cn('inline-flex items-center gap-0.5', className)}>
    {keys.map((k, i) => (
      <kbd key={i} className="px-1.5 py-0.5 text-2xs font-mono bg-surface-overlay border border-border-default rounded text-text-muted">
        {k}
      </kbd>
    ))}
  </span>
);

export default Kbd;
