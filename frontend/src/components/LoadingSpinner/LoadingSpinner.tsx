/**
 * LoadingSpinner Component
 * 
 * An animated loading spinner with size variants for the
 * Disease-Relater application. Features a medical-themed
 * cyan color with smooth animation.
 * 
 * @example
 * // Default medium spinner
 * <LoadingSpinner />
 * 
 * @example
 * // Large spinner with custom label (shown during form submission)
 * <LoadingSpinner size="large" label="Calculating your risk..." />
 * 
 * @example
 * // Small inline spinner
 * <LoadingSpinner size="small" />
 * 
 * @example
 * // Spinner inside a button (prefer Button's isLoading prop instead)
 * <Button disabled>
 *   <LoadingSpinner size="small" /> Processing...
 * </Button>
 * 
 * @example
 * // Full-page loading state
 * <div className="flex items-center justify-center min-h-screen">
 *   <LoadingSpinner size="large" label="Loading disease data..." />
 * </div>
 */

/** Spinner size options */
export type SpinnerSize = 'small' | 'medium' | 'large';

export interface LoadingSpinnerProps {
  /** Spinner size */
  size?: SpinnerSize;
  /** Accessible label for screen readers */
  label?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Animated loading spinner with accessibility support.
 * Uses CSS animation for smooth, performant rotation.
 */
export function LoadingSpinner({
  size = 'medium',
  label = 'Loading',
  className = '',
}: LoadingSpinnerProps) {
  // Size-specific dimensions
  const sizeStyles: Record<SpinnerSize, string> = {
    small: 'w-4 h-4 border-2',
    medium: 'w-8 h-8 border-3',
    large: 'w-12 h-12 border-4',
  };

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 ${className}`}
      role="status"
      aria-live="polite"
    >
      <div
        className={`
          ${sizeStyles[size]}
          border-slate-700 border-t-cyan-500
          rounded-full
          animate-spin
        `}
        style={{
          animationDuration: '0.8s',
          animationTimingFunction: 'linear',
        }}
        aria-hidden="true"
      />
      
      {/* Visible label for larger spinners */}
      {size === 'large' && label && (
        <span className="text-sm text-slate-400 animate-pulse">
          {label}
        </span>
      )}
      
      {/* Screen reader label */}
      <span className="sr-only">{label}</span>
    </div>
  );
}
