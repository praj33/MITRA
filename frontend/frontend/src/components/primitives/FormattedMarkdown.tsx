import React from 'react';

interface Props {
  content: string;
  className?: string;
}

export const FormattedMarkdown: React.FC<Props> = ({ content, className = '' }) => {
  if (!content) return null;

  const lines = content.split('\n');

  return (
    <div className={`space-y-1.5 leading-relaxed ${className}`}>
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();

        // 1. Process bold syntax **text** within each line
        const parts = line.split(/(\*\*.*?\*\*)/g);
        const lineContent = parts.map((part, partIdx) => {
          if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
            const boldText = part.slice(2, -2);
            return (
              <strong key={partIdx} className="font-semibold text-text-primary">
                {boldText}
              </strong>
            );
          }
          return part;
        });

        // Empty line spacer
        if (!trimmed) {
          return <div key={lineIdx} className="h-1.5" />;
        }

        // Bullet point item
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={lineIdx} className="flex items-start gap-2 ml-2 my-1 text-text-secondary">
              <span className="text-brand-light text-xs mt-1">•</span>
              <span>{lineContent.map((item, i) => (typeof item === 'string' ? item.replace(/^[-*]\s+/, '') : item))}</span>
            </div>
          );
        }

        // Numbered list item (e.g. 1. 2. 3.)
        const numMatch = trimmed.match(/^(\d+)\.\s+/);
        if (numMatch) {
          return (
            <div key={lineIdx} className="flex items-start gap-2 ml-2 my-1 text-text-secondary">
              <span className="font-medium text-brand-light text-xs mt-0.5">{numMatch[1]}.</span>
              <span>{lineContent.map((item, i) => (typeof item === 'string' ? item.replace(/^\d+\.\s+/, '') : item))}</span>
            </div>
          );
        }

        // Section header (e.g. **Heading**)
        if (trimmed.startsWith('**') && trimmed.endsWith('**') && trimmed.length > 4) {
          return (
            <div key={lineIdx} className="font-semibold text-sm text-text-primary mt-2 mb-1">
              {trimmed.slice(2, -2)}
            </div>
          );
        }

        // Standard text paragraph
        return (
          <p key={lineIdx} className="text-text-secondary">
            {lineContent}
          </p>
        );
      })}
    </div>
  );
};

export default FormattedMarkdown;
