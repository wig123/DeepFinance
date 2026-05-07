import { forwardRef, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ButtonProps {
  variant?: 'gold' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
  children?: ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'gold',
      size = 'md',
      loading = false,
      icon,
      children,
      className,
      disabled,
      onClick,
      type = 'button',
    },
    ref
  ) => {
    const baseClasses =
      'inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white disabled:opacity-50 disabled:cursor-not-allowed';

    const variantClasses = {
      gold: 'bg-gradient-to-r from-gold-600 to-gold-500 text-white shadow-md shadow-gold-500/20 hover:from-gold-500 hover:to-gold-400 hover:shadow-gold-500/40 focus:ring-gold-500/50',
      secondary:
        'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gold-400/40 hover:text-gray-900 focus:ring-gray-300 shadow-sm',
      ghost:
        'bg-transparent text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:ring-gray-200',
      danger:
        'bg-coral-600 text-white hover:bg-coral-500 focus:ring-coral-500/50',
    };

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-5 py-2.5 text-base',
      lg: 'px-7 py-3 text-lg',
    };

    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        type={type}
        className={cn(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        disabled={isDisabled}
        onClick={onClick}
        whileHover={isDisabled ? undefined : { y: -2, transition: { duration: 0.2 } }}
        whileTap={isDisabled ? undefined : { y: 0, scale: 0.98, transition: { duration: 0.1 } }}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          icon && <span className="flex-shrink-0">{icon}</span>
        )}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
