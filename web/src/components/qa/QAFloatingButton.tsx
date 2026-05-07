import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

interface QAFloatingButtonProps {
  onClick: () => void;
}

export function QAFloatingButton({ onClick }: QAFloatingButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      className="fixed bottom-8 right-8 w-14 h-14 rounded-full bg-gradient-to-br from-gold-400 via-gold-500 to-gold-600 flex items-center justify-center shadow-lg shadow-gold-500/30 hover:shadow-xl hover:shadow-gold-500/40 transition-shadow z-50 group"
    >
      <Sparkles className="w-6 h-6 text-white group-hover:rotate-12 transition-transform" />

      {/* Pulse animation */}
      <motion.div
        className="absolute inset-0 rounded-full bg-gold-400/30"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0, 0.5],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Tooltip */}
      <motion.div
        initial={{ opacity: 0, x: 10 }}
        whileHover={{ opacity: 1, x: 0 }}
        className="absolute right-full mr-3 px-3 py-1.5 rounded-lg bg-white border border-gray-200 whitespace-nowrap pointer-events-none shadow-md"
      >
        <span className="text-sm text-gray-700 font-medium">Ask AI</span>
        <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full w-0 h-0 border-t-4 border-t-transparent border-b-4 border-b-transparent border-l-4 border-l-gray-200" />
      </motion.div>
    </motion.button>
  );
}
