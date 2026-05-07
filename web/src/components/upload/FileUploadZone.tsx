import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { validateFile, formatFileSize, cn } from '../../lib/utils';

interface FileUploadZoneProps {
  onFileSelect: (file: File | null) => void;
  accept?: string;
  maxSize?: number;
  disabled?: boolean;
}

export function FileUploadZone({
  onFileSelect,
  accept = '.pdf',
  maxSize = 50 * 1024 * 1024, // 50MB
  disabled = false,
}: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      const validation = validateFile(file, accept, maxSize);
      if (!validation.valid) {
        setError(validation.error || '文件验证失败');
        return;
      }

      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [accept, maxSize, onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [disabled, handleFile]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) {
        setIsDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const handleRemoveFile = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setSelectedFile(null);
      setError(null);
      onFileSelect(null);
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    },
    [onFileSelect]
  );

  return (
    <div className="w-full">
      <motion.div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300',
          isDragging
            ? 'border-gold-500 bg-gold-500/10'
            : selectedFile
            ? 'border-mint-500/50 bg-mint-500/5'
            : 'border-gray-200 bg-gray-50 hover:border-gold-500/40 hover:bg-gray-100',
          disabled && 'opacity-50 cursor-not-allowed',
          error && 'border-coral-500/50 bg-coral-500/5'
        )}
        animate={isDragging ? { scale: 1.02 } : { scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />

        <AnimatePresence mode="wait">
          {selectedFile ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-xl bg-mint-500/20 flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-mint-400" />
              </div>
              <div className="flex items-center gap-3">
                <div>
                  <p className="text-gray-800 font-medium">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="p-1.5 rounded-lg bg-gray-100 hover:bg-coral-500/10 text-gray-500 hover:text-coral-500 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center"
            >
              <motion.div
                className={cn(
                  'w-16 h-16 rounded-xl flex items-center justify-center mb-4 transition-colors duration-300',
                  isDragging ? 'bg-gold-500/20' : 'bg-gray-100'
                )}
                animate={isDragging ? { y: [0, -5, 0] } : {}}
                transition={{ duration: 0.3 }}
              >
                <Upload
                  className={cn(
                    'w-8 h-8 transition-colors duration-300',
                    isDragging ? 'text-gold-400' : 'text-gray-400'
                  )}
                />
              </motion.div>
              <p className="text-gray-700 font-medium mb-1">
                {isDragging ? '松开以上传文件' : '拖拽文件到此 或 点击上传'}
              </p>
              <p className="text-sm text-gray-400">
                支持 PDF 格式，最大 {formatFileSize(maxSize)}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Decorative elements */}
        <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
          <div
            className={cn(
              'absolute inset-0 transition-opacity duration-300',
              isDragging ? 'opacity-100' : 'opacity-0'
            )}
          >
            <div className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-gold-500/30 to-transparent" />
            <div className="absolute top-0 left-1/2 w-px h-full bg-gradient-to-b from-transparent via-gold-500/20 to-transparent" />
            <div className="absolute top-0 left-3/4 w-px h-full bg-gradient-to-b from-transparent via-gold-500/30 to-transparent" />
          </div>
        </div>
      </motion.div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-2 mt-3 px-4 py-2 bg-coral-500/10 border border-coral-500/30 rounded-lg"
          >
            <AlertCircle className="w-4 h-4 text-coral-400 flex-shrink-0" />
            <p className="text-sm text-coral-300">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
