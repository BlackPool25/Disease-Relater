/**
 * Select Component
 * 
 * A dropdown select component with label support for the
 * Disease-Relater application. Features custom styling that
 * matches the medical-themed design system.
 * 
 * @example
 * // Gender selection
 * <Select
 *   label="Gender"
 *   value={gender}
 *   onChange={(e) => setGender(e.target.value)}
 *   options={[
 *     { value: 'male', label: 'Male' },
 *     { value: 'female', label: 'Female' },
 *   ]}
 *   placeholder="Select gender..."
 * />
 * 
 * @example
 * // Exercise level selection
 * <Select
 *   label="Exercise Level"
 *   value={exerciseLevel}
 *   onChange={(e) => setExerciseLevel(e.target.value)}
 *   options={[
 *     { value: 'sedentary', label: 'Sedentary' },
 *     { value: 'light', label: 'Light Exercise' },
 *     { value: 'moderate', label: 'Moderate Exercise' },
 *     { value: 'active', label: 'Very Active' },
 *   ]}
 * />
 * 
 * @example
 * // Select with error state
 * <Select
 *   label="Smoking Status"
 *   options={smokingOptions}
 *   error={errors.smoking}
 * />
 * 
 * @example
 * // ICD Chapter filter
 * <Select
 *   label="ICD Chapter"
 *   options={chapters.map(c => ({ value: c.code, label: c.name }))}
 *   placeholder="Filter by chapter..."
 * />
 */
import { forwardRef, type SelectHTMLAttributes } from 'react';

/** Option structure for the select dropdown */
export interface SelectOption {
  /** Option value */
  value: string;
  /** Display label */
  label: string;
  /** Whether option is disabled */
  disabled?: boolean;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Select label text */
  label?: string;
  /** Available options */
  options: SelectOption[];
  /** Placeholder text shown when no option is selected */
  placeholder?: string;
  /** Error message to display */
  error?: string;
}

/**
 * Accessible dropdown select with custom styling.
 * Uses forwardRef to support ref forwarding for form libraries.
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, placeholder, error, className = '', id, ...props }, ref) => {
    // Generate stable ID from label if not provided
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="text-sm font-medium text-slate-300"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={`
              w-full px-3 py-2 pr-10
              bg-slate-800 text-slate-100
              border rounded-lg
              appearance-none cursor-pointer
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
            aria-describedby={error ? `${selectId}-error` : undefined}
            {...props}
          >
            {placeholder && (
              <option value="" disabled className="text-slate-500">
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option
                key={opt.value}
                value={opt.value}
                disabled={opt.disabled}
                className="bg-slate-800 text-slate-100"
              >
                {opt.label}
              </option>
            ))}
          </select>
          
          {/* Custom dropdown arrow */}
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg
              className="w-4 h-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>
        
        {error && (
          <span
            id={`${selectId}-error`}
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
      </div>
    );
  }
);

Select.displayName = 'Select';
