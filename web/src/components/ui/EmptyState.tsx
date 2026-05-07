import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { fadeInUp } from '../../lib/animations';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
  compact?: boolean;
}

/**
 * Empty state component for displaying when there's no content
 * Use for empty lists, search results, or initial states
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="initial"
      animate="animate"
      className={cn(
        'flex flex-col items-center justify-center text-center',
        compact ? 'py-8 px-4' : 'py-12 px-6',
        className
      )}
    >
      <div
        className={cn(
          'rounded-full bg-gray-100 flex items-center justify-center mb-4',
          compact ? 'w-12 h-12' : 'w-16 h-16'
        )}
      >
        <div className={cn('text-gray-400', compact ? 'w-6 h-6' : 'w-8 h-8')}>
          {icon}
        </div>
      </div>

      <h3
        className={cn(
          'font-medium text-gray-700 mb-1',
          compact ? 'text-base' : 'text-lg'
        )}
      >
        {title}
      </h3>

      {description && (
        <p
          className={cn(
            'text-gray-400 max-w-xs',
            compact ? 'text-xs mb-3' : 'text-sm mb-4'
          )}
        >
          {description}
        </p>
      )}

      {action && <div className="mt-2">{action}</div>}
    </motion.div>
  );
}
