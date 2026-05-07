import { motion } from 'framer-motion';
import { Check, Loader2 } from 'lucide-react';
import type { PipelineStage, StageName } from '../../types';
import { getStageLabel } from '../../lib/utils';
import { cn } from '../../lib/utils';

interface StepProgressBarProps {
  stages: PipelineStage[];
  className?: string;
}

const STAGE_ORDER: StageName[] = ['parsing', 'analysis', 'research', 'generation'];

export function StepProgressBar({ stages, className }: StepProgressBarProps) {
  const getStageStatus = (stageName: StageName) => {
    const stage = stages.find((s) => s.name === stageName);
    return stage?.status || 'pending';
  };

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        {STAGE_ORDER.map((stageName, index) => {
          const status = getStageStatus(stageName);
          const isCompleted = status === 'completed';
          const isActive = status === 'in_progress';
          const isPending = status === 'pending';
          const isFailed = status === 'failed';

          return (
            <div key={stageName} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center">
                <motion.div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors duration-300',
                    isCompleted && 'bg-mint-500 text-white',
                    isActive && 'bg-gold-500 text-white',
                    isPending && 'bg-gray-100 text-gray-400 border border-gray-200',
                    isFailed && 'bg-coral-500 text-white'
                  )}
                  animate={
                    isActive
                      ? {
                          scale: [1, 1.1, 1],
                          boxShadow: [
                            '0 0 0 0 rgba(245, 158, 11, 0.4)',
                            '0 0 0 10px rgba(245, 158, 11, 0)',
                            '0 0 0 0 rgba(245, 158, 11, 0)',
                          ],
                        }
                      : {}
                  }
                  transition={
                    isActive
                      ? { duration: 1.5, repeat: Infinity, ease: 'easeInOut' }
                      : {}
                  }
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : isActive ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : isFailed ? (
                    <span>!</span>
                  ) : (
                    index + 1
                  )}
                </motion.div>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium transition-colors duration-300',
                    isCompleted && 'text-mint-400',
                    isActive && 'text-gold-400',
                    isPending && 'text-gray-400',
                    isFailed && 'text-coral-400'
                  )}
                >
                  {getStageLabel(stageName)}
                </span>
              </div>

              {/* Connector Line */}
              {index < STAGE_ORDER.length - 1 && (
                <div className="flex-1 mx-2 relative h-0.5">
                  {/* Background line */}
                  <div className="absolute inset-0 bg-gray-200 rounded-full" />
                  {/* Progress line */}
                  <motion.div
                    className={cn(
                      'absolute inset-y-0 left-0 rounded-full',
                      isCompleted
                        ? 'bg-gradient-to-r from-mint-500 to-mint-400'
                        : 'bg-gray-200'
                    )}
                    initial={{ width: '0%' }}
                    animate={{ width: isCompleted ? '100%' : '0%' }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
