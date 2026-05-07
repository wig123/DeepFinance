import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

// Toast types
type ToastType = 'success' | 'error' | 'info' | 'loading';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (type: ToastType, message: string, duration?: number) => string;
  removeToast: (id: string) => void;
  success: (message: string, duration?: number) => string;
  error: (message: string, duration?: number) => string;
  info: (message: string, duration?: number) => string;
  loading: (message: string) => string;
}

const ToastContext = createContext<ToastContextValue | null>(null);

// Generate unique ID
let toastId = 0;
const generateId = () => `toast-${++toastId}`;

// Toast Provider
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, message: string, duration?: number) => {
      const id = generateId();
      const toast: Toast = {
        id,
        type,
        message,
        duration: duration ?? (type === 'loading' ? 0 : 4000),
      };

      setToasts((prev) => [...prev, toast]);

      // Auto-dismiss (except loading)
      if (toast.duration && toast.duration > 0) {
        setTimeout(() => removeToast(id), toast.duration);
      }

      return id;
    },
    [removeToast]
  );

  const success = useCallback(
    (message: string, duration?: number) => addToast('success', message, duration),
    [addToast]
  );

  const error = useCallback(
    (message: string, duration?: number) => addToast('error', message, duration ?? 6000),
    [addToast]
  );

  const info = useCallback(
    (message: string, duration?: number) => addToast('info', message, duration),
    [addToast]
  );

  const loading = useCallback(
    (message: string) => addToast('loading', message, 0),
    [addToast]
  );

  return (
    <ToastContext.Provider
      value={{ toasts, addToast, removeToast, success, error, info, loading }}
    >
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

// Hook to use toast
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// Toast Container
function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>
  );
}

// Single Toast Item
function ToastItem({
  toast,
  onRemove,
}: {
  toast: Toast;
  onRemove: (id: string) => void;
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [progress, setProgress] = useState(100);

  // Progress bar animation
  useEffect(() => {
    if (!toast.duration || toast.duration === 0 || isHovered) return;

    const interval = 50;
    const decrement = (100 * interval) / toast.duration;

    const timer = setInterval(() => {
      setProgress((prev) => Math.max(0, prev - decrement));
    }, interval);

    return () => clearInterval(timer);
  }, [toast.duration, isHovered]);

  const config = {
    success: {
      icon: <CheckCircle2 className="w-5 h-5" />,
      bg: 'bg-mint-500/10',
      border: 'border-mint-500/30',
      iconColor: 'text-mint-400',
      progressColor: 'bg-mint-500',
    },
    error: {
      icon: <AlertCircle className="w-5 h-5" />,
      bg: 'bg-coral-500/10',
      border: 'border-coral-500/30',
      iconColor: 'text-coral-400',
      progressColor: 'bg-coral-500',
    },
    info: {
      icon: <Info className="w-5 h-5" />,
      bg: 'bg-electric-500/10',
      border: 'border-electric-500/30',
      iconColor: 'text-electric-400',
      progressColor: 'bg-electric-500',
    },
    loading: {
      icon: <Loader2 className="w-5 h-5 animate-spin" />,
      bg: 'bg-gold-500/10',
      border: 'border-gold-500/30',
      iconColor: 'text-gold-400',
      progressColor: 'bg-gold-500',
    },
  };

  const { icon, bg, border, iconColor, progressColor } = config[toast.type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        'pointer-events-auto relative overflow-hidden',
        'min-w-[280px] max-w-[400px]',
        'backdrop-blur-xl rounded-xl border shadow-lg',
        bg,
        border
      )}
    >
      <div className="flex items-center gap-3 p-4">
        <span className={cn('flex-shrink-0', iconColor)}>{icon}</span>
        <p className="flex-1 text-sm text-gray-800">{toast.message}</p>
        {toast.type !== 'loading' && (
          <button
            onClick={() => onRemove(toast.id)}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      {toast.duration && toast.duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-200">
          <motion.div
            className={cn('h-full', progressColor)}
            initial={{ width: '100%' }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.05, ease: 'linear' }}
          />
        </div>
      )}
    </motion.div>
  );
}
