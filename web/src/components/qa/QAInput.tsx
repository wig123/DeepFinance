import { useState, useRef, type KeyboardEvent } from 'react';
import { Send, Loader2, Square } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface QAInputProps {
  onSubmit: (question: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

export function QAInput({
  onSubmit,
  onStop,
  disabled = false,
  isStreaming = false,
  placeholder = '提问关于报告的问题...',
}: QAInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!input.trim() || disabled || isStreaming) return;

    onSubmit(input.trim());
    setInput('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleStop = () => {
    onStop?.();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Escape to stop streaming
    if (e.key === 'Escape' && isStreaming) {
      e.preventDefault();
      handleStop();
      return;
    }
    
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={isStreaming ? '生成中... 按 Esc 停止' : placeholder}
            disabled={disabled || isStreaming}
            rows={1}
            className="w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gold-500/50 focus:border-gold-500/50 disabled:opacity-50 disabled:cursor-not-allowed resize-none transition-all"
          />
        </div>

        <AnimatePresence mode="wait">
          {isStreaming ? (
            <motion.button
              key="stop"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={handleStop}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-coral-500 hover:bg-coral-600 flex items-center justify-center transition-all hover:shadow-lg hover:shadow-coral-500/25"
              title="停止生成 (Esc)"
            >
              <Square className="w-4 h-4 text-white fill-current" />
            </motion.button>
          ) : (
            <motion.button
              key="send"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={handleSubmit}
              disabled={!input.trim() || disabled}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:shadow-gold-500/25"
              title="发送 (Enter)"
            >
              <Send className="w-5 h-5 text-white" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      <p className="mt-2 text-xs text-gray-400 text-center">
        {isStreaming ? '按 Esc 停止生成' : '按 Enter 发送，Shift + Enter 换行'}
      </p>
    </div>
  );
}
