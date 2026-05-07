import { motion } from 'framer-motion';
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import type { PipelineStage, StageStatus, StageName } from '../../types';
import { ProgressBar, Card } from '../ui';
import { formatDuration, getStageLabel, getStageDescription, cn } from '../../lib/utils';
import { fadeInUp } from '../../lib/animations';

interface StageCardProps {
  stage: PipelineStage;
  index: number;
}

const stageIcons: Record<StageName, string> = {
  parsing: '📄',
  analysis: '🔍',
  research: '🌐',
  generation: '✨',
};

export function StageCard({ stage, index }: StageCardProps) {
  const { name, status, duration, details } = stage;

  const statusConfig: Record<
    StageStatus,
    { icon: React.ReactNode; color: string; bgColor: string }
  > = {
    pending: {
      icon: <Clock className="w-5 h-5" />,
      color: 'text-gray-400',
      bgColor: 'bg-gray-100',
    },
    in_progress: {
      icon: <Loader2 className="w-5 h-5 animate-spin" />,
      color: 'text-gold-400',
      bgColor: 'bg-gold-500/20',
    },
    completed: {
      icon: <CheckCircle2 className="w-5 h-5" />,
      color: 'text-mint-400',
      bgColor: 'bg-mint-500/20',
    },
    failed: {
      icon: <XCircle className="w-5 h-5" />,
      color: 'text-coral-400',
      bgColor: 'bg-coral-500/20',
    },
  };

  const { icon, color, bgColor } = statusConfig[status];

  return (
    <motion.div
      variants={fadeInUp}
      initial="initial"
      animate="animate"
      transition={{ delay: index * 0.1 }}
    >
      <Card
        variant={status === 'in_progress' ? 'active' : 'default'}
        padding="md"
      >
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={cn(
              'flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
              bgColor
            )}
          >
            <span className="text-2xl">{stageIcons[name]}</span>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-display font-semibold text-gray-900">
                  {index + 1}. {getStageLabel(name)}
                </h3>
                <span className={cn(color)}>{icon}</span>
              </div>
              {duration && (
                <span className="text-sm text-gray-400">
                  {formatDuration(duration)}
                </span>
              )}
            </div>

            <p className="text-sm text-gray-500 mb-3">
              {getStageDescription(name)}
            </p>

            {/* Progress Bar */}
            {status === 'in_progress' && details && (
              <div className="mb-3">
                <ProgressBar
                  progress={calculateProgress(name, details)}
                  showLabel
                />
              </div>
            )}

            {/* Details */}
            {details && Object.keys(details).length > 0 && (
              <div className="space-y-1 text-sm">
                {renderStageDetails(name, status, details)}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

// Calculate progress based on stage details
function calculateProgress(
  stage: StageName,
  details: Record<string, unknown>
): number {
  switch (stage) {
    case 'parsing':
      if (details.pages_extracted && details.total_pages) {
        return Number(details.pages_extracted) / Number(details.total_pages);
      }
      return 0;
    case 'analysis':
      if (details.sections_completed && details.total_sections) {
        return Number(details.sections_completed) / Number(details.total_sections);
      }
      return 0;
    case 'research':
      if (details.queries_completed && details.total_queries) {
        return Number(details.queries_completed) / Number(details.total_queries);
      }
      return 0;
    default:
      return 0;
  }
}

// Render stage-specific details
function renderStageDetails(
  stage: StageName,
  status: StageStatus,
  details: Record<string, unknown>
) {
  const detailItems: React.ReactNode[] = [];

  switch (stage) {
    case 'parsing':
      if (details.pages_extracted) {
        detailItems.push(
          <DetailItem
            key="pages"
            label="已提取页面"
            value={`${details.pages_extracted}${details.total_pages ? ` / ${details.total_pages}` : ''} 页`}
            status={status}
          />
        );
      }
      if (details.figures_count) {
        detailItems.push(
          <DetailItem
            key="figures"
            label="识别图表"
            value={`${details.figures_count} 个`}
            status={status}
          />
        );
      }
      if (details.tables_count) {
        detailItems.push(
          <DetailItem
            key="tables"
            label="提取表格"
            value={`${details.tables_count} 个`}
            status={status}
          />
        );
      }
      break;

    case 'analysis':
      if (details.sections_completed !== undefined) {
        detailItems.push(
          <DetailItem
            key="sections"
            label="分析进度"
            value={`${details.sections_completed}${details.total_sections ? ` / ${details.total_sections}` : ''} 部分`}
            status={status}
          />
        );
      }
      if (details.current_section) {
        detailItems.push(
          <DetailItem
            key="current"
            label="当前处理"
            value={String(details.current_section)}
            status={status}
          />
        );
      }
      if (details.metrics_extracted) {
        detailItems.push(
          <DetailItem
            key="metrics"
            label="发现指标"
            value={`${details.metrics_extracted} 个`}
            status={status}
          />
        );
      }
      break;

    case 'research':
      if (details.queries_completed !== undefined) {
        detailItems.push(
          <DetailItem
            key="queries"
            label="搜索查询"
            value={`${details.queries_completed}${details.total_queries ? ` / ${details.total_queries}` : ''}`}
            status={status}
          />
        );
      }
      if (details.current_query) {
        detailItems.push(
          <DetailItem
            key="current"
            label="当前查询"
            value={String(details.current_query)}
            status={status}
            truncate
          />
        );
      }
      if (details.results_found) {
        detailItems.push(
          <DetailItem
            key="results"
            label="找到结果"
            value={`${details.results_found} 条`}
            status={status}
          />
        );
      }
      break;

    case 'generation':
      if (details.report_url) {
        detailItems.push(
          <div key="complete" className="flex items-center gap-2 text-mint-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>报告已生成</span>
          </div>
        );
      }
      break;
  }

  return detailItems;
}

// Detail Item Component
interface DetailItemProps {
  label: string;
  value: string;
  status: StageStatus;
  truncate?: boolean;
}

function DetailItem({ label, value, status, truncate }: DetailItemProps) {
  const valueColor =
    status === 'completed'
      ? 'text-gray-700'
      : status === 'in_progress'
      ? 'text-gold-600'
      : 'text-gray-500';

  return (
    <div className="flex items-center gap-2">
      <span className="text-gray-400">├─</span>
      <span className="text-gray-500">{label}:</span>
      <span className={cn(valueColor, truncate && 'truncate max-w-[200px]')}>
        {value}
      </span>
    </div>
  );
}
