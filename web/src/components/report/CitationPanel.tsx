import { motion } from 'framer-motion';
import {
  X,
  FileText,
  Globe,
  ExternalLink,
  MapPin,
} from 'lucide-react';
import { getFileUrl } from '../../api';
import { getCitationType, getCitationLabel, getCitationIcon, cn } from '../../lib/utils';
import { Card } from '../ui';
import { slideInFromRight } from '../../lib/animations';
import type { ParsedCitation } from './ReportViewer';

interface CitationPanelProps {
  citationId: string | null;
  citation: ParsedCitation | null;
  projectId: string;
  onClose: () => void;
}

export function CitationPanel({
  citationId,
  citation,
  projectId,
  onClose,
}: CitationPanelProps) {
  const type = citationId ? getCitationType(citationId) : null;
  const label = type ? getCitationLabel(type) : '';
  const icon = type ? getCitationIcon(type) : '';

  const headerBgClass = {
    document: 'bg-electric-500/10 border-electric-500/30',
    chart: 'bg-mint-500/10 border-mint-500/30',
    web: 'bg-gold-500/10 border-gold-500/30',
  };

  const headerIconClass = {
    document: 'text-electric-400',
    chart: 'text-mint-400',
    web: 'text-gold-400',
  };

  return (
    <motion.div
      variants={slideInFromRight}
      initial="initial"
      animate="animate"
      exit="exit"
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center justify-between px-4 py-3 border-b',
          type ? headerBgClass[type] : 'bg-white border-gray-200'
        )}
      >
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <h3 className={cn('font-medium', type && headerIconClass[type])}>
            {label}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {citation ? (
          <div className="space-y-4">
            {citation.type === 'document' && (
              <DocumentCitationView citation={citation} />
            )}
            {citation.type === 'chart' && (
              <ChartCitationView
                citation={citation}
                projectId={projectId}
              />
            )}
            {citation.type === 'web' && (
              <WebCitationView
                citation={{ ...citation, citation_id: citationId || undefined }}
              />
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            点击报告中的引用标注查看详情
          </div>
        )}
      </div>

      {/* Citation ID */}
      {citationId && (
        <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>引用ID:</span>
            <code className="font-mono bg-gray-100 px-2 py-0.5 rounded">
              {citationId}
            </code>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// Document Citation View
function DocumentCitationView({ citation }: { citation: ParsedCitation }) {
  // Parse location to extract section title
  const locationParts = citation.location?.split('#') || [];
  const sectionTitle = citation.title || (locationParts.length > 1
    ? locationParts[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    : citation.location);

  return (
    <div className="space-y-4">
      {/* Section Title */}
      <Card variant="solid" padding="md">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-electric-500/20 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-electric-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-gray-800 mb-1">文档章节</h4>
            <p className="text-sm text-electric-400">{sectionTitle}</p>
            {locationParts[0] && (
              <p className="text-xs text-gray-400 mt-1 truncate">
                {locationParts[0]}
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Original Text Excerpt (English) */}
      {citation.source && (
        <Card variant="solid" padding="md" className="border-l-4 border-electric-500/50">
          <h5 className="font-medium text-gray-700 mb-2 flex items-center gap-2 text-sm">
            <span className="text-electric-400">📝</span>
            英文原文
          </h5>
          <blockquote className="text-sm text-gray-700 leading-relaxed font-serif">
            "{citation.source}"
          </blockquote>
          {/* Note: Chinese translation can be added here if needed */}
        </Card>
      )}

      {/* Location hint */}
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <MapPin className="w-3.5 h-3.5" />
        <span>来源：原始文档</span>
      </div>
    </div>
  );
}

// Chart Citation View
function ChartCitationView({
  citation,
  projectId,
}: {
  citation: ParsedCitation;
  projectId: string;
}) {
  // Build image URL from imagePath or url
  const imageUrl = citation.url || (citation.imagePath
    ? getFileUrl(projectId, citation.imagePath.startsWith('source/') ? citation.imagePath : `source/${citation.imagePath}`)
    : '');

  return (
    <div className="space-y-4">
      {/* Chart Title */}
      {citation.title && (
        <div className="flex items-center gap-2">
          <span className="text-mint-400">📊</span>
          <h4 className="text-lg font-medium text-gray-800">
            {citation.title}
          </h4>
        </div>
      )}

      {/* Image with zoom capability */}
      <div className="rounded-xl border border-mint-500/30 overflow-hidden bg-white shadow-lg">
        <img
          src={imageUrl}
          alt={citation.title || citation.id}
          className="w-full h-auto cursor-zoom-in hover:scale-105 transition-transform duration-300"
          onClick={() => window.open(imageUrl, '_blank')}
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150"><rect fill="%23f1f5f9" width="200" height="150"/><text x="100" y="75" text-anchor="middle" fill="%2394a3b8" font-size="14">图表加载失败</text></svg>';
          }}
        />
      </div>
      <p className="text-xs text-gray-400 text-center">点击图片放大查看</p>

      {/* File Reference */}
      {citation.imagePath && (
        <div className="flex items-center gap-2 text-gray-400 text-xs font-mono bg-gray-100 px-3 py-2 rounded-lg">
          <span>📁</span>
          <span className="truncate">{citation.imagePath}</span>
        </div>
      )}
    </div>
  );
}

// Web Citation View
function WebCitationView({ citation }: { citation: ParsedCitation & { citation_id?: string } }) {
  // Extract domain from URL for display
  const getDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace('www.', '');
    } catch {
      return url;
    }
  };

  // Get source type badge from citation ID
  const getSourceBadge = (citationId?: string): { label: string; color: string } | null => {
    if (!citationId) return null;

    if (citationId.startsWith('temporal-') || citationId.includes('-temporal-')) {
      return { label: '时间序列', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' };
    }
    if (citationId.startsWith('compare-') || citationId.includes('-compare-')) {
      return { label: '对比分析', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' };
    }
    if (citationId.startsWith('deepdive-') || citationId.includes('-deepdive-')) {
      return { label: '深度研究', color: 'bg-rose-500/20 text-rose-400 border-rose-500/30' };
    }
    if (citationId.startsWith('market-') || citationId.includes('-market-')) {
      return { label: '市场情报', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' };
    }
    if (citationId.startsWith('gap-')) {
      return { label: '补充研究', color: 'bg-gold-500/20 text-gold-400 border-gold-500/30' };
    }
    return null;
  };

  // Get favicon URL
  const getFaviconUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=32`;
    } catch {
      return '';
    }
  };

  const domain = citation.url ? getDomain(citation.url) : '';
  const sourceBadge = getSourceBadge(citation.citation_id);
  const faviconUrl = citation.url ? getFaviconUrl(citation.url) : '';

  return (
    <div className="space-y-4">
      {/* Source Type Badge */}
      {sourceBadge && (
        <div className="flex items-center gap-2">
          <span className={cn(
            'px-2.5 py-1 text-xs font-medium rounded-full border',
            sourceBadge.color
          )}>
            {sourceBadge.label}
          </span>
        </div>
      )}

      {/* Title & Link Card */}
      <a
        href={citation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block rounded-xl border border-gold-500/30 overflow-hidden hover:border-gold-500/50 transition-colors group"
      >
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-gold-500/10 to-amber-500/10 px-4 py-3 border-b border-gold-500/20">
          <div className="flex items-start gap-3">
            {/* Favicon or Globe icon */}
            <div className="w-8 h-8 rounded-lg bg-gold-500/20 flex items-center justify-center flex-shrink-0 overflow-hidden">
              {faviconUrl ? (
                <img
                  src={faviconUrl}
                  alt=""
                  className="w-5 h-5"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    (e.target as HTMLImageElement).parentElement!.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gold-400"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>';
                  }}
                />
              ) : (
                <Globe className="w-5 h-5 text-gold-400" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gold-300 group-hover:text-gold-200 transition-colors line-clamp-2 leading-tight">
                {citation.title || '外部资源'}
              </h4>
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-xs text-gray-500 truncate">{domain}</span>
                <ExternalLink className="w-3 h-3 text-gray-500 flex-shrink-0" />
              </div>
            </div>
          </div>
        </div>

        {/* URL display */}
        <div className="px-4 py-2 bg-gray-50">
          <p className="text-xs text-gray-400 truncate font-mono">{citation.url}</p>
        </div>
      </a>

      {/* Source badge */}
      <div className="flex items-center gap-1.5 text-xs text-gray-500 bg-gray-100 px-2.5 py-1.5 rounded-lg w-fit">
        <Globe className="w-3.5 h-3.5" />
        <span>网络来源</span>
      </div>
    </div>
  );
}
