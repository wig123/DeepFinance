import { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Lightbulb, Trash2, RefreshCw } from 'lucide-react';
import { QAMessage as QAMessageComponent } from './QAMessage';
import { QAInput } from './QAInput';
import { QASuggestions } from './QASuggestions';
import { QASkeleton } from './QASkeleton';
import { useQASession } from '../../hooks/useQASession';
import type { QAMessage } from '../../types';
import { useQAStream } from '../../hooks/useQAStream';

interface QAPanelProps {
  projectId: string;
  onClose: () => void;
  onCitationClick?: (citationId: string) => void;
}

export function QAPanel({ projectId, onClose, onCitationClick }: QAPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Session management
  const {
    session,
    sessionId,
    suggestions,
    isLoading: isSessionLoading,
    refreshSession,
    createSession,
  } = useQASession(projectId);

  // Streaming
  const {
    answer,
    isStreaming,
    error: streamError,
    lastQuestion,
    ask,
    stop,
    retry,
  } = useQAStream({
    projectId,
    sessionId: sessionId || '',
    onDone: () => {
      // Refresh session to get the saved message
      setTimeout(() => refreshSession(), 500);
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages, answer]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to focus input (handled by QAInput)
      if (e.key === 'Escape' && !isStreaming) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isStreaming, onClose]);

  const handleAsk = useCallback(
    (question: string) => {
      if (!sessionId || isStreaming) return;
      setShowSuggestions(false);
      ask(question, 'basic');
    },
    [sessionId, isStreaming, ask]
  );

  const handleSuggestionSelect = useCallback(
    (question: string) => {
      handleAsk(question);
    },
    [handleAsk]
  );

  const handleClearSession = useCallback(async () => {
    if (window.confirm('确定要清空当前对话吗？')) {
      await createSession();
    }
  }, [createSession]);

  const toggleSuggestions = useCallback(() => {
    setShowSuggestions((prev) => !prev);
  }, []);

  const hasMessages = session?.messages && session.messages.length > 0;
  const showInitialSuggestions = !hasMessages && suggestions.length > 0 && !showSuggestions;

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <div>
            <h3 className="text-lg font-display font-semibold text-gray-900">Ask AI</h3>
            <p className="text-xs text-gray-500">关于报告的智能问答</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle suggestions button */}
          {suggestions.length > 0 && hasMessages && (
            <button
              onClick={toggleSuggestions}
              className={`p-2 rounded-lg transition-colors ${
                showSuggestions
                  ? 'bg-gold-500/20 text-gold-400'
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
              }`}
              title="推荐问题"
            >
              <Lightbulb className="w-4 h-4" />
            </button>
          )}

          {/* Clear session button */}
          {hasMessages && (
            <button
              onClick={handleClearSession}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
              title="清空对话"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}

          {/* Close button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
            title="关闭 (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {isSessionLoading && !session ? (
          <QASkeleton />
        ) : (
          <>
            {/* Suggestions (show on toggle or initially) */}
            <AnimatePresence>
              {(showInitialSuggestions || showSuggestions) && suggestions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <QASuggestions
                    suggestions={suggestions}
                    onSelect={handleSuggestionSelect}
                    disabled={isStreaming}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Messages */}
            {session?.messages.map((message: QAMessage, idx: number) => (
              <QAMessageComponent
                key={`${message.timestamp}-${message.role}-${idx}`}
                message={message}
                onCitationClick={onCitationClick}
                onRegenerate={
                  message.role === 'assistant' && idx === session.messages.length - 1
                    ? retry
                    : undefined
                }
              />
            ))}

            {/* Streaming answer */}
            {isStreaming && answer && (
              <QAMessageComponent
                message={{
                  role: 'assistant',
                  content: answer,
                  timestamp: new Date().toISOString(),
                }}
                onCitationClick={onCitationClick}
                isStreaming={true}
                showActions={false}
              />
            )}

            {/* Stream error with retry */}
            <AnimatePresence>
              {streamError && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-coral-500/20 border border-coral-500/30 rounded-lg px-4 py-3"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-coral-400">⚠️ {streamError}</p>
                    {lastQuestion && (
                      <button
                        onClick={retry}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-coral-500/20 hover:bg-coral-500/30 text-coral-300 text-sm transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        重试
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <QAInput
        onSubmit={handleAsk}
        onStop={stop}
        disabled={!sessionId || isSessionLoading}
        isStreaming={isStreaming}
      />
    </div>
  );
}
