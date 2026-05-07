import { cn } from '../../lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'default' | 'circular' | 'text';
}

/**
 * Skeleton loading placeholder component
 * Use to indicate content is loading and prevent layout shift
 */
export function Skeleton({ className, variant = 'default' }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-gray-200',
        variant === 'circular' && 'rounded-full',
        variant === 'text' && 'rounded h-4',
        variant === 'default' && 'rounded-lg',
        className
      )}
    />
  );
}

/**
 * Pre-built skeleton for project list items in sidebar
 */
export function ProjectListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-2 px-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="p-3 rounded-lg">
          <Skeleton className="h-4 w-3/4 mb-2" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Pre-built skeleton for report content
 */
export function ReportSkeleton() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Title */}
      <Skeleton className="h-10 w-2/3 mb-8" />

      {/* Paragraphs */}
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
      </div>

      {/* Section header */}
      <Skeleton className="h-7 w-1/3 mt-8" />

      {/* More paragraphs */}
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>

      {/* Table skeleton */}
      <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
        <div className="bg-gray-100 p-3">
          <div className="flex gap-4">
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-1/4" />
            <Skeleton className="h-4 w-1/4" />
          </div>
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-3 border-t border-gray-200">
            <div className="flex gap-4">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Pre-built skeleton for card content
 */
export function CardSkeleton() {
  return (
    <div className="glass-card p-5 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" className="w-10 h-10" />
        <div className="flex-1">
          <Skeleton className="h-5 w-1/2 mb-2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
    </div>
  );
}
