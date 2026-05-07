/**
 * PDF 查看器组件
 * 基于 react-pdf-highlighter-extended，支持滚动到指定位置并高亮
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  PdfLoader,
  PdfHighlighter,
  AreaHighlight,
  useHighlightContainerContext,
} from 'react-pdf-highlighter-extended';
import type {
  PdfHighlighterUtils,
  Highlight,
  Scaled,
} from 'react-pdf-highlighter-extended';
import type { PDFHighlight } from '../../types';
import PDFToolbar from './PDFToolbar';

interface PDFViewerProps {
  /** PDF 文件 URL */
  url: string;
  /** 要高亮显示的区域 */
  highlight?: PDFHighlight | null;
  /** 关闭回调 */
  onClose?: () => void;
}

/**
 * 将我们的 PDFHighlight 格式转换为 react-pdf-highlighter-extended 的 Highlight 格式
 * 
 * 重要：Scaled 类型的 x1/y1/x2/y2 是**绝对像素坐标**，不是 0-1 比例值！
 * 库内部使用公式 `left = viewportWidth * x1 / width` 来计算视口位置。
 */
function convertToLibraryHighlight(pdfHighlight: PDFHighlight): Highlight {
  const { page_number, bounding_rect, page_dimensions } = pdfHighlight;


  // Scaled 类型：
  // - x1/y1/x2/y2：绝对像素坐标（例如 72, 286.36）
  // - width/height：**必须是页面尺寸**，用于计算比例
  // 库使用公式 left = viewportWidth * x1 / width 计算视口位置
  // 所以 width/height 应该是页面尺寸（例如 612, 792）
  // 这样 x1=8.52 时，left = viewport * 8.52 / 612 ≈ 1.4%
  const boundingRect: Scaled = {
    x1: bounding_rect.x1,  // 高亮框左边界的像素坐标
    y1: bounding_rect.y1,  // 高亮框上边界的像素坐标
    x2: bounding_rect.x2,  // 高亮框右边界的像素坐标
    y2: bounding_rect.y2,  // 高亮框下边界的像素坐标
    width: page_dimensions.width,   // **页面**宽度（用于比例计算）
    height: page_dimensions.height, // **页面**高度（用于比例计算）
    pageNumber: page_number,
  };


  return {
    id: `highlight-${page_number}-${Date.now()}`,
    type: 'area',
    position: {
      boundingRect,
      rects: [boundingRect],
    },
  };
}

/**
 * 高亮渲染组件
 */
function HighlightRenderer() {
  const { highlight, isScrolledTo } = useHighlightContainerContext();


  return (
    <AreaHighlight
      highlight={highlight}
      isScrolledTo={isScrolledTo}
      onChange={() => {}}
      style={{
        background: 'rgba(255, 215, 0, 0.4)',  // 改为黄色
        border: '3px solid rgb(255, 180, 0)',
        boxShadow: isScrolledTo ? '0 0 20px rgba(255, 215, 0, 0.6)' : 'none',
        transition: 'all 0.3s ease',
        mixBlendMode: 'multiply',
      }}
    />
  );
}

export default function PDFViewer({ url, highlight, onClose }: PDFViewerProps) {
  const [scale, setScale] = useState<number>(1.0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const highlighterUtilsRef = useRef<PdfHighlighterUtils | null>(null);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const hasScrolledRef = useRef(false);
  const prevHighlightRef = useRef<PDFHighlight | null>(null);
  const [utilsReady, setUtilsReady] = useState(false);

  // 当 highlight 变化时，转换并设置高亮
  useEffect(() => {
    if (highlight) {
      const libHighlight = convertToLibraryHighlight(highlight);
      setHighlights([libHighlight]);
      setCurrentPage(highlight.page_number);

      // 检查是否是新的 highlight（不同的页码或位置）
      const isNewHighlight =
        !prevHighlightRef.current ||
        prevHighlightRef.current.page_number !== highlight.page_number ||
        prevHighlightRef.current.bounding_rect.x1 !== highlight.bounding_rect.x1 ||
        prevHighlightRef.current.bounding_rect.y1 !== highlight.bounding_rect.y1;

      if (isNewHighlight) {
        hasScrolledRef.current = false;
        setUtilsReady(false);
        prevHighlightRef.current = highlight;
      }
    } else {
      setHighlights([]);
      prevHighlightRef.current = null;
    }
  }, [highlight, utilsReady]);

  // 滚动到高亮位置 - 使用库提供的 scrollToHighlight 方法，并调整为居中显示
  useEffect(() => {
    if (
      highlights.length > 0 &&
      utilsReady &&
      !hasScrolledRef.current &&
      highlighterUtilsRef.current
    ) {
      hasScrolledRef.current = true;
      const targetHighlight = highlights[0];

      // 延迟确保页面渲染完成
      setTimeout(() => {
        if (highlighterUtilsRef.current) {
          try {
            // 首先使用库方法滚动到高亮位置（会滚动到顶部）
            highlighterUtilsRef.current.scrollToHighlight(targetHighlight);

            // 然后调整滚动位置使高亮居中显示
            setTimeout(() => {
              const viewer = highlighterUtilsRef.current?.getViewer();
              if (viewer?.container) {
                const container = viewer.container;
                const viewportHeight = container.clientHeight;

                // 检查 viewportHeight 是否有效，避免容器未渲染时的错误调整
                if (viewportHeight <= 0) return;

                // 找到高亮元素获取其高度
                const highlightElement = container.querySelector('.AreaHighlight__part');
                const highlightHeight = highlightElement?.getBoundingClientRect().height || 100;

                // 计算需要向下滚动的偏移量，使高亮居中
                const centerOffset = (viewportHeight / 2) - (highlightHeight / 2) - 50;

                // 向上滚动使高亮居中（减去偏移量）
                container.scrollTop = Math.max(0, container.scrollTop - centerOffset);
              }
            }, 100);
          } catch {
            // scrollToHighlight failed silently
          }
        }
      }, 300);
    }
  }, [highlights, utilsReady]);

  const handleZoomIn = useCallback(() => {
    setScale((prev) => Math.min(prev + 0.25, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  }, []);

  const handleZoomReset = useCallback(() => {
    setScale(1.0);
  }, []);

  return (
    <div className="flex flex-col h-full bg-gray-900">
      <PDFToolbar
        currentPage={currentPage}
        totalPages={totalPages}
        scale={scale}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onZoomReset={handleZoomReset}
        onClose={onClose}
      />

      <div className="flex-1 overflow-hidden relative">
        <PdfLoader
          document={url}
          workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs"
          beforeLoad={() => (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-400">
                <svg
                  className="animate-spin h-8 w-8 mx-auto mb-2"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span>加载 PDF 中...</span>
              </div>
            </div>
          )}
          errorMessage={(error) => (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-400 text-center">
                <p className="mb-2">PDF 加载失败</p>
                <p className="text-sm text-gray-500">{error.message}</p>
              </div>
            </div>
          )}
        >
          {(pdfDocument) => {
            // 使用 queueMicrotask 延迟设置状态，避免在渲染过程中更新
            if (pdfDocument.numPages !== totalPages) {
              queueMicrotask(() => setTotalPages(pdfDocument.numPages));
            }

            return (
              <PdfHighlighter
                pdfDocument={pdfDocument}
                highlights={highlights}
                pdfScaleValue={scale}
                utilsRef={(utils) => {
                  highlighterUtilsRef.current = utils;
                  queueMicrotask(() => setUtilsReady(true));
                }}
                style={{
                  height: '100%',
                  overflow: 'auto',
                }}
              >
                <HighlightRenderer />
              </PdfHighlighter>
            );
          }}
        </PdfLoader>
      </div>
    </div>
  );
}
