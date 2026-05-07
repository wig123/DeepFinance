import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

interface QASuggestionsProps {
  suggestions: string[];
  onSelect: (question: string) => void;
  disabled?: boolean;
}

export function QASuggestions({ suggestions, onSelect, disabled = false }: QASuggestionsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="px-4 py-3 space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-gold-400" />
        <h4 className="text-sm font-medium text-gray-700">推荐问题</h4>
      </div>

      <div className="space-y-2">
        {suggestions.map((suggestion, idx) => (
          <motion.button
            key={idx}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            onClick={() => onSelect(suggestion)}
            disabled={disabled}
            className="w-full text-left px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 hover:border-gold-400/50 hover:bg-gray-100 transition-all text-sm text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <span className="block group-hover:text-gold-400 transition-colors">
              {suggestion}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
