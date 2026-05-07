import { motion } from 'framer-motion';

export function QASkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Suggestions skeleton */}
      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-4 h-4 rounded bg-gray-200" />
          <div className="h-4 w-20 rounded bg-gray-200" />
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="w-full h-12 rounded-lg bg-gray-100 border border-gray-200"
          />
        ))}
      </div>

      {/* Message skeleton */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex gap-3"
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-2/3" />
        </div>
      </motion.div>

      {/* Loading indicator */}
      <div className="flex items-center justify-center py-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gold-400 animate-bounce [animation-delay:-0.3s]" />
          <div className="w-2 h-2 rounded-full bg-gold-400 animate-bounce [animation-delay:-0.15s]" />
          <div className="w-2 h-2 rounded-full bg-gold-400 animate-bounce" />
        </div>
        <span className="ml-3 text-sm text-gray-400">初始化会话中...</span>
      </div>
    </div>
  );
}
