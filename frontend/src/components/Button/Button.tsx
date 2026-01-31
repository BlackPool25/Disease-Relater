/**
 * Button Component
 * 
 * A versatile button component with primary/secondary variants for the
 * Disease-Relater application. Features medical-themed styling with
 * cyan/teal accents and smooth transitions.
 * 
 * @example
 * // Primary submit button for forms
 * <Button variant="primary" onClick={handleSubmit}>
 *   Calculate Risk
 * </Button>
 * 
 * @example
 * // Loading state during API calls
 * <Button variant="primary" isLoading disabled>
 *   Calculating...
 * </Button>
 * 
 * @example
 * // Secondary navigation button
 * <Button variant="secondary" onClick={goToPrevStep}>
 *   ← Previous
 * </Button>
 * 
 * @example
 * // Danger button for destructive actions
 * <Button variant="danger" onClick={handleReset}>
 *   Reset Form
 * </Button>
 * 
 * @example
 * // Ghost button for subtle actions
 * <Button variant="ghost" size="sm">
 *   Skip
 * </Button>
 */
import { type ButtonHTMLAttributes, type ReactNode } from 'react';

/** Button visual variants */
export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

/** Button size options */
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant */
  variant?: ButtonVariant;
  /** Button size */
  size?: ButtonSize;
  /** Button content */
  children: ReactNode;
  /** Show loading spinner */
  isLoading?: boolean;
}

/**
 * Primary action button with medical-themed styling.
 * Uses cyan as primary color to align with data visualization theme.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  children,
  disabled,
  isLoading,
  className = '',
  ...props
}: ButtonProps) {
  // Base styles for all buttons
  const baseStyles = `
    inline-flex items-center justify-center gap-2
    font-medium rounded-lg
    transition-all duration-200 ease-out
    focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
    disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
  `;

  // Size variants
  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  // Visual variants with medical-themed colors
  const variantStyles: Record<ButtonVariant, string> = {
    primary: `
      bg-cyan-600 text-white
      hover:bg-cyan-500 hover:shadow-lg hover:shadow-cyan-500/25
      active:bg-cyan-700
      focus-visible:ring-cyan-500
    `,
    secondary: `
      bg-slate-700 text-slate-100 border border-slate-600
      hover:bg-slate-600 hover:border-slate-500
      active:bg-slate-800
      focus-visible:ring-slate-500
    `,
    danger: `
      bg-red-600 text-white
      hover:bg-red-500 hover:shadow-lg hover:shadow-red-500/25
      active:bg-red-700
      focus-visible:ring-red-500
    `,
    ghost: `
      bg-transparent text-slate-300
      hover:bg-slate-800 hover:text-slate-100
      active:bg-slate-700
      focus-visible:ring-slate-500
    `,
  };

  return (
    <button
      className={`
        ${baseStyles}
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
