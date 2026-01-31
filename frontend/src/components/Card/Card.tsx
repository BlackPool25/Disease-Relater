/**
 * Card Component
 * 
 * A container component with title and variant styles for the
 * Disease-Relater application. Features glass-morphism effects
 * and semantic color variants for different states.
 * 
 * @example
 * // Form section card
 * <Card title="Personal Information">
 *   <Input label="Age" type="number" />
 *   <Select label="Gender" options={genderOptions} />
 * </Card>
 * 
 * @example
 * // Results card with glow effect
 * <Card title="Risk Assessment Results" variant="info" glow>
 *   <p>Your calculated risk score: 0.75</p>
 * </Card>
 * 
 * @example
 * // Error state card
 * <Card variant="danger" title="Error">
 *   <p>Unable to calculate risk. Please try again.</p>
 * </Card>
 * 
 * @example
 * // Success card with footer
 * <Card
 *   variant="success"
 *   title="Calculation Complete"
 *   footer={<Button variant="primary">View Details</Button>}
 * >
 *   <p>Your risk assessment is ready.</p>
 * </Card>
 * 
 * @example
 * // Simple content card without title
 * <Card className="p-6">
 *   <LoadingSpinner size="large" label="Loading diseases..." />
 * </Card>
 */
import { type ReactNode } from 'react';

/** Card visual variants */
export type CardVariant = 'default' | 'danger' | 'success' | 'warning' | 'info';

export interface CardProps {
  /** Card title */
  title?: string;
  /** Card content */
  children: ReactNode;
  /** Visual variant for different states */
  variant?: CardVariant;
  /** Additional CSS classes */
  className?: string;
  /** Optional footer content */
  footer?: ReactNode;
  /** Whether to show subtle border glow */
  glow?: boolean;
}

/**
 * Container card with glass-morphism effect and semantic variants.
 * Ideal for displaying disease information, statistics, or form sections.
 */
export function Card({
  title,
  children,
  variant = 'default',
  className = '',
  footer,
  glow = false,
}: CardProps) {
  // Variant-specific border and background colors
  const variantStyles: Record<CardVariant, string> = {
    default: 'border-slate-700/50 bg-slate-800/70',
    danger: 'border-red-500/30 bg-red-950/30',
    success: 'border-green-500/30 bg-green-950/30',
    warning: 'border-yellow-500/30 bg-yellow-950/30',
    info: 'border-cyan-500/30 bg-cyan-950/30',
  };

  // Title color based on variant
  const titleColors: Record<CardVariant, string> = {
    default: 'text-slate-100',
    danger: 'text-red-300',
    success: 'text-green-300',
    warning: 'text-yellow-300',
    info: 'text-cyan-300',
  };

  // Glow effect color
  const glowStyles: Record<CardVariant, string> = {
    default: 'shadow-cyan-500/10',
    danger: 'shadow-red-500/20',
    success: 'shadow-green-500/20',
    warning: 'shadow-yellow-500/20',
    info: 'shadow-cyan-500/20',
  };

  return (
    <div
      className={`
        rounded-xl border backdrop-blur-md
        transition-all duration-200
        ${variantStyles[variant]}
        ${glow ? `shadow-lg ${glowStyles[variant]}` : 'shadow-sm'}
        ${className}
      `}
    >
      {/* Card header */}
      {title && (
        <div className="px-4 py-3 border-b border-slate-700/50">
          <h3 className={`text-lg font-semibold ${titleColors[variant]}`}>
            {title}
          </h3>
        </div>
      )}

      {/* Card content */}
      <div className="p-4">
        {children}
      </div>

      {/* Card footer */}
      {footer && (
        <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-900/30 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
}
