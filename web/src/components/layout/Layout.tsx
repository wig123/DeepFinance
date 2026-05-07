import { type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '../sidebar/Sidebar';
import { cn } from '../../lib/utils';

interface LayoutProps {
  children: ReactNode;
  sidePanel?: ReactNode;
  showSidePanel?: boolean;
  onCloseSidePanel?: () => void;
  /** 分屏内容 (如 PDF Viewer) */
  splitContent?: ReactNode;
  /** 是否显示分屏 */
  showSplitView?: boolean;
  /** 关闭分屏回调 */
  onCloseSplitView?: () => void;
}

export function Layout({
  children,
  sidePanel,
  showSidePanel = false,
  splitContent,
  showSplitView = false,
  onCloseSplitView,
}: LayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Grid Background */}
      <div className="fixed inset-0 grid-bg pointer-events-none" />

      {/* Project Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Content Area */}
        <div
          className={cn(
            'flex-1 overflow-auto transition-all duration-300',
            showSidePanel && !showSplitView && 'mr-0 lg:mr-[440px]',
            showSplitView && 'lg:w-1/2 lg:flex-none'
          )}
        >
          {children}
        </div>

        {/* Split View - PDF Viewer (Desktop) */}
        <AnimatePresence>
          {showSplitView && splitContent && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: '50%', opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="hidden lg:block h-full border-l border-gray-200 overflow-hidden"
            >
              {splitContent}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Split View - PDF Viewer (Mobile Modal) */}
        <AnimatePresence>
          {showSplitView && splitContent && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={onCloseSplitView}
                className="fixed inset-0 bg-black/80 z-50 lg:hidden"
              />
              {/* Full Screen Panel */}
              <motion.div
                initial={{ y: '100%' }}
                animate={{ y: 0 }}
                exit={{ y: '100%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="fixed inset-0 bg-white z-50 lg:hidden"
              >
                {splitContent}
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Side Panel (Citation Panel) - Only show when not in split view */}
        <AnimatePresence>
          {showSidePanel && sidePanel && !showSplitView && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 440, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed right-0 top-0 h-full bg-white border-l border-gray-200 overflow-hidden z-40 hidden lg:block shadow-xl"
            >
              {sidePanel}
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Mobile Side Panel - Modal */}
        <AnimatePresence>
          {showSidePanel && sidePanel && !showSplitView && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              />
              {/* Panel */}
              <motion.aside
                initial={{ y: '100%' }}
                animate={{ y: 0 }}
                exit={{ y: '100%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                className="fixed bottom-0 left-0 right-0 h-[70vh] bg-white rounded-t-3xl border-t border-gray-200 overflow-hidden z-50 lg:hidden shadow-xl"
              >
                {/* Drag Handle */}
                <div className="flex justify-center py-3">
                  <div className="w-10 h-1 rounded-full bg-gray-300" />
                </div>
                {sidePanel}
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
