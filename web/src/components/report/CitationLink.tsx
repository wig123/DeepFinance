import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getCitationType, getCitationLabel, getCitationIcon, cn } from '../../lib/utils';
import { tooltipVariants } from '../../lib/animations';
import type { CitationType } from '../../types';

interface CitationLinkProps {
  citationId: string;
  onClick: (id: string) => void;
  children?: React.ReactNode;
}

export function CitationLink({ citationId, onClick, children }: CitationLinkProps) {
  const [showPreview, setShowPreview] = useState(false);

  const type = getCitationType(citationId);
  const label = getCitationLabel(type);
  const icon = getCitationIcon(type);

  const badgeClasses: Record<CitationType, string> = {
    document: 'citation-badge-doc',
    chart: 'citation-badge-chart',
    web: 'citation-badge-web',
  };

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setShowPreview(true)}
      onMouseLeave={() => setShowPreview(false)}
    >
      <motion.sup
        className={cn('citation-badge cursor-pointer', badgeClasses[type])}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onClick(citationId);
        }}
        title={`${label}: ${citationId}`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        transition={{ duration: 0.15 }}
      >
        {children || citationId}
      </motion.sup>

      {/* Hover Preview - use span instead of div to avoid nesting issues in <p> */}
      <AnimatePresence>
        {showPreview && (
          <motion.span
            variants={tooltipVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 pointer-events-none block"
          >
            <span className="block px-3 py-2 bg-white border border-gray-200 rounded-lg shadow-lg whitespace-nowrap">
              <span className="flex items-center gap-2">
                <span className="text-base">{icon}</span>
                <span className="text-sm text-gray-700">{label}</span>
              </span>
              <span className="block text-xs text-gray-400 mt-1">
                {type === 'web' ? '点击打开链接' : '点击查看详情'}
              </span>
            </span>
            {/* Arrow */}
            <span className="absolute left-1/2 -translate-x-1/2 top-full block">
              <span className="block w-2 h-2 bg-white border-r border-b border-gray-200 transform rotate-45 -translate-y-1" />
            </span>
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
}
