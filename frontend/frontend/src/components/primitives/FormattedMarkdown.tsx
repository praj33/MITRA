import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface Props {
  content: string;
  className?: string;
}

/**
 * Normalizes LaTeX math delimiters while protecting code blocks from transformation:
 * - \[ ... \] -> $$ ... $$ (display math)
 * - \( ... \) -> $ ... $ (inline math)
 */
function normalizeLatexDelimiters(content: string): string {
  if (!content) return '';

  const parts = content.split(/(```[\s\S]*?```|`[^`\n]+`)/g);

  return parts
    .map((part, index) => {
      // Code blocks and inline code are at odd indices — leave them untouched
      if (index % 2 === 1) return part;

      return part
        .replace(/\\\[([\s\S]*?)\\\]/g, (_, math) => `\n\n$$\n${math.trim()}\n$$\n\n`)
        .replace(/\\\(([\s\S]*?)\\\)/g, (_, math) => `$${math.trim()}$`);
    })
    .join('');
}

export const FormattedMarkdown: React.FC<Props> = ({ content, className = '' }) => {
  const normalized = useMemo(() => normalizeLatexDelimiters(content), [content]);

  if (!content) return null;

  return (
    <div
      className={`formatted-markdown text-sm leading-relaxed text-text-primary min-w-0 max-w-full overflow-hidden ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-text-primary mt-4 mb-2 first:mt-0 tracking-tight">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold text-text-primary mt-3.5 mb-1.5 first:mt-0 tracking-tight">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-text-primary mt-3 mb-1 first:mt-0">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold text-text-primary mt-2 mb-1 first:mt-0">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="text-text-secondary leading-relaxed my-1.5 first:mt-0 last:mb-0">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-text-primary">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-text-primary/90">
              {children}
            </em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-outside ml-4 my-2 space-y-1 text-text-secondary">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside ml-4 my-2 space-y-1 text-text-secondary">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-1 marker:text-brand-light">
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-brand-dim pl-3.5 py-1 my-2.5 text-text-muted italic bg-surface-elevated/40 rounded-r">
              {children}
            </blockquote>
          ),
          hr: () => (
            <hr className="border-border-subtle my-3" />
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-light hover:underline font-medium underline-offset-2 break-all"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 rounded-lg border border-border-subtle max-w-full">
              <table className="w-full text-left text-xs border-collapse divide-y divide-border-subtle">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-surface-elevated text-text-primary font-medium">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-border-subtle/60 bg-surface-raised/40">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-surface-hover/30 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="py-2 px-3 font-semibold text-text-primary text-xs">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="py-2 px-3 text-text-secondary align-top text-xs">
              {children}
            </td>
          ),
          pre: ({ children }) => (
            <div className="my-2.5 rounded-lg border border-border-subtle bg-surface-elevated overflow-hidden max-w-full">
              <pre className="p-3 text-xs font-mono text-text-primary overflow-x-auto leading-normal">
                {children}
              </pre>
            </div>
          ),
          code: ({ className: codeClassName, children, ...rest }: any) => {
            // If code is inside pre, ReactMarkdown passes pre -> code
            // Check if it's inline or block
            const isInline = !codeClassName && typeof children === 'string' && !children.includes('\n');
            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-surface-elevated text-brand-light font-mono text-xs border border-border-subtle select-all"
                  {...rest}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...rest}>
                {children}
              </code>
            );
          },
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
};

export default FormattedMarkdown;
