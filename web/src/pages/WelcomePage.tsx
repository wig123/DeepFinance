import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Clock, FileSearch } from 'lucide-react';
import { FileUploadZone } from '../components/upload/FileUploadZone';
import { Button } from '../components/ui';
import { createProject } from '../api';
import type { AnalysisMode } from '../types';
import { cn } from '../lib/utils';
import { fadeInUp, staggerContainer, staggerItem } from '../lib/animations';

export function WelcomePage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [userQuery, setUserQuery] = useState('');
  const [mode, setMode] = useState<AnalysisMode>('full');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showQuery, setShowQuery] = useState(false);

  const handleSubmit = async () => {
    if (!file) return;

    setIsSubmitting(true);
    try {
      const response = await createProject(file, userQuery || undefined, mode);
      navigate(`/projects/${response.project_id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 lg:p-8">
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <motion.div variants={staggerItem} className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-gold-500/10 border border-gold-500/20 rounded-full mb-6">
            <Sparkles className="w-4 h-4 text-gold-400" />
            <span className="text-sm text-gold-400 font-medium">
              AI 驱动的文档分析
            </span>
          </div>

          <h1 className="text-4xl lg:text-5xl font-display font-bold text-gray-900 mb-4">
            <span className="text-gradient-gold">DeepFinance</span>
          </h1>
          <p className="text-lg text-gray-500 max-w-md mx-auto">
            上传金融文档，获取深度分析报告。
            <br />
            自动提取数据、分析趋势、生成洞察。
          </p>
        </motion.div>

        {/* Upload Section */}
        <motion.div variants={staggerItem}>
          <div className="glass-card p-6 lg:p-8">
            <FileUploadZone
              onFileSelect={setFile}
              accept=".pdf"
              maxSize={50 * 1024 * 1024}
              disabled={isSubmitting}
            />

            {/* User Query Section */}
            <motion.div
              initial={false}
              animate={{ height: showQuery ? 'auto' : 'auto' }}
              className="mt-6"
            >
              <button
                onClick={() => setShowQuery(!showQuery)}
                className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-3"
              >
                <span className="text-lg">📝</span>
                <span>描述您的分析需求（可选）</span>
                <motion.span
                  animate={{ rotate: showQuery ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="text-xs"
                >
                  ▼
                </motion.span>
              </button>

              {showQuery && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <textarea
                    value={userQuery}
                    onChange={(e) => setUserQuery(e.target.value)}
                    placeholder="例如：重点分析利润率变化和现金流状况，关注 Q4 指引..."
                    maxLength={500}
                    rows={3}
                    className="input-field resize-none"
                    disabled={isSubmitting}
                  />
                  <div className="flex justify-end mt-1">
                    <span className="text-xs text-gray-400">
                      {userQuery.length}/500
                    </span>
                  </div>
                </motion.div>
              )}
            </motion.div>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 text-sm text-gray-400 bg-white">
                  选择分析模式
                </span>
              </div>
            </div>

            {/* Mode Selection */}
            <div className="grid grid-cols-3 gap-3">
              <ModeCard
                mode="minimal"
                selected={mode === 'minimal'}
                onClick={() => setMode('minimal')}
                icon={<Zap className="w-5 h-5" />}
                title="快速模式"
                description="跳过图片分析和研究"
                time="~1 分钟"
                disabled={isSubmitting}
              />
              <ModeCard
                mode="no-research"
                selected={mode === 'no-research'}
                onClick={() => setMode('no-research')}
                icon={<FileSearch className="w-5 h-5" />}
                title="文档分析"
                description="深度分析，无外部研究"
                time="~2 分钟"
                disabled={isSubmitting}
              />
              <ModeCard
                mode="full"
                selected={mode === 'full'}
                onClick={() => setMode('full')}
                icon={<Sparkles className="w-5 h-5" />}
                title="完整分析"
                description="图片分析 + 外部研究"
                time="~3 分钟"
                disabled={isSubmitting}
                recommended
              />
            </div>

            {/* Submit Button */}
            <div className="mt-8">
              <Button
                variant="gold"
                size="lg"
                className="w-full"
                onClick={handleSubmit}
                disabled={!file || isSubmitting}
                loading={isSubmitting}
              >
                {isSubmitting ? '正在上传...' : '开始分析'}
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Features */}
        <motion.div
          variants={staggerItem}
          className="mt-8 grid grid-cols-3 gap-4"
        >
          {[
            { icon: '📊', label: '图表分析', desc: '自动识别和解读' },
            { icon: '🔍', label: '深度研究', desc: '补充外部数据' },
            { icon: '📝', label: '溯源系统', desc: '每句话可追溯' },
          ].map((feature, index) => (
            <motion.div
              key={feature.label}
              variants={fadeInUp}
              transition={{ delay: 0.1 * index }}
              className="text-center p-4 rounded-xl bg-white border border-gray-100 shadow-sm"
            >
              <span className="text-2xl">{feature.icon}</span>
              <p className="text-sm font-medium text-gray-700 mt-2">
                {feature.label}
              </p>
              <p className="text-xs text-gray-400 mt-1">{feature.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}

// Mode Card Component
interface ModeCardProps {
  mode: AnalysisMode;
  selected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
  disabled?: boolean;
  recommended?: boolean;
}

function ModeCard({
  selected,
  onClick,
  icon,
  title,
  description,
  time,
  disabled,
  recommended,
}: ModeCardProps) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? undefined : { scale: 1.02 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      className={cn(
        'relative p-4 rounded-xl text-left transition-all duration-300 border-2',
        selected
          ? 'bg-gold-500/10 border-gold-500/50'
          : 'bg-white border-gray-200 hover:border-gray-300',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      {recommended && (
        <span className="absolute -top-2 right-3 px-2 py-0.5 bg-gold-500 text-navy-950 text-xs font-medium rounded">
          推荐
        </span>
      )}

      <div
        className={cn(
          'w-10 h-10 rounded-lg flex items-center justify-center mb-3 transition-colors',
          selected ? 'bg-gold-500/20 text-gold-400' : 'bg-gray-100 text-gray-500'
        )}
      >
        {icon}
      </div>

      <h3
        className={cn(
          'font-semibold mb-1 transition-colors',
          selected ? 'text-gold-400' : 'text-gray-700'
        )}
      >
        {title}
      </h3>
      <p className="text-xs text-gray-400 mb-2">{description}</p>

      <div className="flex items-center gap-1 text-xs text-gray-400">
        <Clock className="w-3 h-3" />
        <span>{time}</span>
      </div>
    </motion.button>
  );
}
