/**
 * PDF 工具栏组件
 * 提供缩放、页码显示、关闭等功能
 */

interface PDFToolbarProps {
  currentPage: number;
  totalPages: number;
  scale: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  onClose?: () => void;
}

export default function PDFToolbar({
  currentPage,
  totalPages,
  scale,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onClose,
}: PDFToolbarProps) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
      {/* 页码信息 */}
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <span>
          页码: {currentPage} / {totalPages || '-'}
        </span>
      </div>

      {/* 缩放控制 */}
      <div className="flex items-center gap-2">
        <button
          onClick={onZoomOut}
          className="p-1.5 rounded hover:bg-gray-700 text-gray-300 transition-colors"
          title="缩小"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 12H4"
            />
          </svg>
        </button>

        <button
          onClick={onZoomReset}
          className="px-2 py-1 text-sm text-gray-300 hover:bg-gray-700 rounded transition-colors min-w-[60px]"
          title="重置缩放"
        >
          {Math.round(scale * 100)}%
        </button>

        <button
          onClick={onZoomIn}
          className="p-1.5 rounded hover:bg-gray-700 text-gray-300 transition-colors"
          title="放大"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </button>
      </div>

      {/* 关闭按钮 */}
      {onClose && (
        <button
          onClick={onClose}
          className="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
          title="关闭"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
