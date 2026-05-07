import type { CitationType, StageName } from '../types';

// ==================== Class Name Utilities ====================

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

// ==================== Time Formatting ====================

export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return '刚刚';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} 天前`;

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ==================== File Utilities ====================

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function validateFile(
  file: File,
  accept: string,
  maxSize: number
): { valid: boolean; error?: string } {
  // Check file type
  const acceptedTypes = accept.split(',').map((t) => t.trim().toLowerCase());
  const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;
  const fileType = file.type.toLowerCase();

  const typeValid = acceptedTypes.some(
    (t) => t === fileExt || t === fileType || t === '*'
  );

  if (!typeValid) {
    return {
      valid: false,
      error: `不支持的文件类型。请上传 ${accept} 格式的文件`,
    };
  }

  // Check file size
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `文件过大。最大支持 ${formatFileSize(maxSize)}`,
    };
  }

  return { valid: true };
}

// ==================== Citation Utilities ====================

export function getCitationType(citationId: string): CitationType {
  // Document citations: doc-p3, doc-section-name, doc-financial-001
  if (citationId.startsWith('doc-')) return 'document';

  // Chart citations: fig-001, fig_003, p4_fig_003.png
  if (
    citationId.startsWith('fig-') ||
    citationId.startsWith('fig_') ||
    citationId.includes('_fig_') ||
    citationId.includes('.png')
  ) {
    return 'chart';
  }

  // External research citations: gap-temporal-001, gap-compare-001, gap-deepdive-001, gap-market-001
  if (
    citationId.startsWith('gap-') ||
    citationId.startsWith('temporal-') ||
    citationId.startsWith('compare-') ||
    citationId.startsWith('deepdive-') ||
    citationId.startsWith('market-')
  ) {
    return 'web';
  }

  return 'document'; // default
}

export function extractCitationId(text: string): string | null {
  // Match patterns like [^doc-p5], [^fig_004.png], [^gap-001-2]
  const match = text.match(/\[\^([^\]]+)\]/);
  return match ? match[1] : null;
}

export function getCitationLabel(type: CitationType): string {
  switch (type) {
    case 'document':
      return '文档引用';
    case 'chart':
      return '图表引用';
    case 'web':
      return '外部研究';
    default:
      return '引用';
  }
}

export function getCitationIcon(type: CitationType): string {
  switch (type) {
    case 'document':
      return '📄';
    case 'chart':
      return '📊';
    case 'web':
      return '🌐';
    default:
      return '📎';
  }
}

// ==================== Stage Utilities ====================

export function getStageLabel(stage: StageName): string {
  switch (stage) {
    case 'parsing':
      return '文档解析';
    case 'analysis':
      return '智能分析';
    case 'research':
      return '外部研究';
    case 'generation':
      return '报告生成';
    default:
      return stage;
  }
}

export function getStageDescription(stage: StageName): string {
  switch (stage) {
    case 'parsing':
      return '提取文档内容、图表和表格';
    case 'analysis':
      return '分析财务数据和关键指标';
    case 'research':
      return '搜索补充数据和最新信息';
    case 'generation':
      return '生成深度分析报告';
    default:
      return '';
  }
}

export function getStageIndex(stage: StageName): number {
  const stages: StageName[] = ['parsing', 'analysis', 'research', 'generation'];
  return stages.indexOf(stage);
}

// ==================== Misc Utilities ====================

export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}
