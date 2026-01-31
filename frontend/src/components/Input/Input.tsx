/**
 * Input Component
 * 
 * A text input component with label and error state support for the
 * Disease-Relater application. Features accessible design with
 * clear focus states and error feedback.
 * 
 * @example
 * // Basic input with label
 * <Input
 *   label="Age"
 *   type="number"
 *   value={age}
 *   onChange={(e) => setAge(e.target.value)}
 *   placeholder="Enter your age"
 * />
 * 
 * @example
 * // Input with error state
 * <Input
 *   label="Weight (kg)"
 *   type="number"
 *   value={weight}
 *   onChange={(e) => setWeight(e.target.value)}
 *   error={errors.weight}
 * />
 * 
 * @example
 * // Input with helper text
 * <Input
 *   label="Height (cm)"
 *   type="number"
 *   helperText="Enter your height in centimeters"
 * />
 * 
 * @example
 * // Search input
 * <Input
 *   type="search"
 *   placeholder="Search diseases..."
 *   className="w-full"
 * />
 */
import { forwardRef, type InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Input label text */
  label?: string;
  /** Error message to display */
  error?: string;
  /** Helper text below the input */
  helperText?: string;
}

/**
 * Accessible text input with label and error state.
 * Uses forwardRef to support ref forwarding for form libraries.
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    // Generate stable ID from label if not provided
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-slate-300"
          >
            {label}
          </label>
        )}
        
        <input
          ref={ref}
          id={inputId}
          className={`
            w-full px-3 py-2
            bg-slate-800 text-slate-100
            border rounded-lg
            placeholder:text-slate-500
            transition-all duration-200
            focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error
              ? 'border-red-500 focus-visible:ring-red-500'
              : 'border-slate-600 hover:border-slate-500 focus-visible:ring-cyan-500'
            }
            ${className}
          `}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={
            error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
          }
          {...props}
        />
        
        {error && (
          <span
            id={`${inputId}-error`}
            className="text-sm text-red-400 flex items-center gap-1.5"
            role="alert"
          >
            <svg
              className="w-4 h-4 shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </span>
        )}
        
        {helperText && !error && (
          <span
            id={`${inputId}-helper`}
            className="text-sm text-slate-500"
          >
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
