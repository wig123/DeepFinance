import { motion } from 'framer-motion';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { StepProgressBar, Button, Card } from '../ui';
import { StageCard } from './StageCard';
import { usePipelineProgress } from '../../hooks/usePipelineProgress';
import { staggerContainer, staggerItem } from '../../lib/animations';

interface PipelineProgressProps {
  projectId: string;
  onComplete: () => void;
}

export function PipelineProgress({
  projectId,
  onComplete,
}: PipelineProgressProps) {
  const { stages, currentMessage, isComplete, error, reconnect } =
    usePipelineProgress({
      projectId,
      onComplete,
    });

  return (
    <div className="max-w-3xl mx-auto p-6 lg:p-8">
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="space-y-8"
      >
        {/* Header */}
        <motion.div variants={staggerItem} className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-gold-500/10 border border-gold-500/20 rounded-full mb-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              className="w-4 h-4 border-2 border-gold-400/30 border-t-gold-400 rounded-full"
            />
            <span className="text-sm text-gold-400 font-medium">
              正在分析您的文档
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-display font-bold text-gray-900 mb-2">
            {currentMessage || '准备中...'}
          </h1>
          <p className="text-gray-500">请稍候，这可能需要几分钟时间</p>
        </motion.div>

        {/* Step Progress Bar */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <StepProgressBar stages={stages} />
          </Card>
        </motion.div>

        {/* Error Alert */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 bg-coral-500/10 border border-coral-500/30 rounded-xl"
          >
            <AlertCircle className="w-5 h-5 text-coral-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-coral-300">{error}</p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={reconnect}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              重试
            </Button>
          </motion.div>
        )}

        {/* Stage Cards */}
        <div className="space-y-4">
          {stages.map((stage, index) => (
            <StageCard key={stage.name} stage={stage} index={index} />
          ))}
        </div>

        {/* Completion Message */}
        {isComplete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <Card variant="active" padding="lg">
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-mint-500/20 flex items-center justify-center mb-4">
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{
                      type: 'spring',
                      stiffness: 200,
                      delay: 0.2,
                    }}
                    className="text-3xl"
                  >
                    ✨
                  </motion.span>
                </div>
                <h2 className="text-xl font-display font-semibold text-mint-400 mb-2">
                  分析完成！
                </h2>
                <p className="text-gray-500 mb-6">
                  您的深度分析报告已生成完毕
                </p>
                <Button variant="gold" onClick={onComplete}>
                  查看报告
                </Button>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Tips Section */}
        {!isComplete && !error && (
          <motion.div variants={staggerItem}>
            <Card variant="solid" padding="md">
              <div className="flex items-start gap-3">
                <span className="text-xl">💡</span>
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-1">
                    小提示
                  </h4>
                  <p className="text-sm text-slate-500">
                    分析过程中会自动提取文档中的关键数据、图表和财务指标，并补充最新的外部信息。
                    完成后您将获得一份可溯源的深度分析报告。
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
