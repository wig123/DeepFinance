import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface ProgressBarProps {
  progress: number; // 0-1
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  variant?: 'default' | 'gold' | 'gradient';
}

export function ProgressBar({
  progress,
  showLabel = false,
  size = 'md',
  className,
  variant = 'gradient',
}: ProgressBarProps) {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-1.5',
    lg: 'h-2',
  };

  const variantClasses = {
    default: 'bg-electric-500',
    gold: 'bg-gold-500',
    gradient: 'bg-gradient-to-r from-gold-500 to-mint-500',
  };

  const clampedProgress = Math.min(Math.max(progress, 0), 1);

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'w-full bg-gray-200 rounded-full overflow-hidden',
          sizeClasses[size]
        )}
      >
        <motion.div
          className={cn('h-full rounded-full', variantClasses[variant])}
          initial={{ width: 0 }}
          animate={{ width: `${clampedProgress * 100}%` }}
          transition={{
            type: 'spring',
            stiffness: 50,
            damping: 20,
          }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-400 mt-1 text-right">
          {Math.round(clampedProgress * 100)}%
        </div>
      )}
    </div>
  );
}
