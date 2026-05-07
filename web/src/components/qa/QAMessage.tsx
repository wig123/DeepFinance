import { memo, useMemo, useState, useCallback } from 'react';
import { User, Sparkles, Copy, Check, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import type { QAMessage as QAMessageType } from '../../types';

interface QAMessageProps {
  message: QAMessageType;
  onCitationClick?: (citationId: string) => void;
  onRegenerate?: () => void;
  isStreaming?: boolean;
  showActions?: boolean;
}

// Memoized markdown components to prevent re-creation on each render
const createMarkdownComponents = (onCitationClick?: (citationId: string) => void) => ({
  p: ({ children }: { children: React.ReactNode }) => (
    <p className="text-sm text-gray-700 mb-2 last:mb-0">{children}</p>
  ),
  a: ({ href, children }: { href?: string; children: React.ReactNode }) => {
    // Check if it's a citation link
    if (href?.startsWith('#')) {
      const citationId = href.slice(1).replace('^', '');
      return (
        <a
          href={href}
          className="text-gold-400 hover:text-gold-300 cursor-pointer underline decoration-gold-400/50 underline-offset-2"
          onClick={(e) => {
            e.preventDefault();
            onCitationClick?.(citationId);
          }}
        >
          {children}
        </a>
      );
    }
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-gold-400 hover:text-gold-300"
      >
        {children}
      </a>
    );
  },
  ul: ({ children }: { children: React.ReactNode }) => (
    <ul className="list-disc pl-4 space-y-1 text-sm text-gray-700">{children}</ul>
  ),
  ol: ({ children }: { children: React.ReactNode }) => (
    <ol className="list-decimal pl-4 space-y-1 text-sm text-gray-700">{children}</ol>
  ),
  li: ({ children }: { children: React.ReactNode }) => (
    <li className="text-gray-700">{children}</li>
  ),
  code: ({ children }: { children: React.ReactNode }) => (
    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono text-gold-600">
      {children}
    </code>
  ),
  strong: ({ children }: { children: React.ReactNode }) => (
    <strong className="font-semibold text-gray-900">{children}</strong>
  ),
  blockquote: ({ children }: { children: React.ReactNode }) => (
    <blockquote className="border-l-2 border-gold-500/50 pl-3 my-2 text-gray-600 italic">
      {children}
    </blockquote>
  ),
});

export const QAMessage = memo(function QAMessage({
  message,
  onCitationClick,
  onRegenerate,
  isStreaming = false,
  showActions = true,
}: QAMessageProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  // Memoize markdown components
  const markdownComponents = useMemo(
    () => createMarkdownComponents(onCitationClick),
    [onCitationClick]
  );

  // Copy to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [message.content]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex gap-3 group ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
      )}

      <div className="flex flex-col max-w-[85%]">
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gold-500/20 border border-gold-500/30'
              : 'bg-gray-50 border border-gray-200'
          }`}
        >
          {isUser ? (
            <p className="text-sm text-gray-900">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown components={markdownComponents}>
                {message.content}
              </ReactMarkdown>
              {/* Typing cursor for streaming */}
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-gold-400 animate-pulse ml-0.5 align-middle" />
              )}
            </div>
          )}

          {/* Citations */}
          {message.citations && message.citations.length > 0 && !isUser && (
            <div className="mt-2 pt-2 border-t border-gray-200 flex flex-wrap gap-1">
              {message.citations.slice(0, 3).map((citation, idx) => (
                <button
                  key={idx}
                  onClick={() => onCitationClick?.(citation)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-500 hover:text-gold-600 hover:bg-gold-500/10 hover:ring-1 hover:ring-gold-500/30 transition-all"
                >
                  {citation}
                </button>
              ))}
              {message.citations.length > 3 && (
                <span className="text-xs text-gray-400 px-2 py-1">
                  +{message.citations.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Action buttons for assistant messages */}
        {!isUser && showActions && !isStreaming && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-1 mt-1 ml-1 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                title={copied ? '已复制' : '复制'}
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
              {onRegenerate && (
                <button
                  onClick={onRegenerate}
                  className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                  title="重新生成"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
          <User className="w-4 h-4 text-gray-500" />
        </div>
      )}
    </motion.div>
  );
});
