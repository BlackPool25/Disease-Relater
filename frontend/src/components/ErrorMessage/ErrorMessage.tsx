/**
 * ErrorMessage Component
 * 
 * An error message display component with optional retry action for the
 * Disease-Relater application. Features accessible error presentation
 * with clear visual hierarchy.
 * 
 * @example
 * // Simple error message
 * <ErrorMessage message="Failed to load diseases" />
 * 
 * @example
 * // Error with retry button (for API failures)
 * <ErrorMessage
 *   message="Failed to calculate risk"
 *   onRetry={() => refetch()}
 * />
 * 
 * @example
 * // Error with details
 * <ErrorMessage
 *   message="Network error"
 *   details="Please check your internet connection and try again."
 *   onRetry={handleRetry}
 * />
 * 
 * @example
 * // Custom retry button label
 * <ErrorMessage
 *   message="Session expired"
 *   onRetry={handleLogin}
 *   retryLabel="Log in again"
 * />
 * 
 * @example
 * // Inline error in a form
 * {apiError && (
 *   <ErrorMessage
 *     message={apiError.message}
 *     onRetry={handleSubmit}
 *     className="mt-4"
 *   />
 * )}
 */
import { Button } from '../Button';

export interface ErrorMessageProps {
  /** Error message to display */
  message: string;
  /** Optional detailed error description */
  details?: string;
  /** Optional retry callback */
  onRetry?: () => void;
  /** Retry button label */
  retryLabel?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Error message display with optional retry functionality.
 * Uses danger variant styling with clear visual feedback.
 */
export function ErrorMessage({
  message,
  details,
  onRetry,
  retryLabel = 'Try again',
  className = '',
}: ErrorMessageProps) {
  return (
    <div
      className={`
        rounded-lg border border-red-500/30 bg-red-950/30
        p-4 flex flex-col gap-3
        ${className}
      `}
      role="alert"
      aria-live="assertive"
    >
      {/* Error header with icon */}
      <div className="flex items-start gap-3">
        <div className="shrink-0 mt-0.5">
          <svg
            className="w-5 h-5 text-red-400"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-red-300 font-medium">
            {message}
          </p>
          
          {details && (
            <p className="mt-1 text-sm text-red-400/80">
              {details}
            </p>
          )}
        </div>
      </div>

      {/* Retry button */}
      {onRetry && (
        <div className="flex justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
            className="border-red-500/30 hover:border-red-500/50"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
