/**
 * Disease-Relater UI Components Library
 * 
 * This module exports all reusable UI components for the Disease-Relater
 * frontend application. Components follow a medical/scientific design
 * theme with cyan/teal accents and glass-morphism effects on a dark
 * slate background.
 * 
 * ============================================================================
 * COMPONENT → FORM USAGE MAPPING
 * ============================================================================
 * 
 * Use these components in form pages instead of custom CSS classes:
 * 
 * | Component      | Form Usage                                          |
 * |----------------|-----------------------------------------------------|
 * | Button         | Navigation buttons, submit button, reset button     |
 * | Input          | Age, height, weight, search fields (type="number")  |
 * | Select         | Gender, exercise level, smoking status dropdowns    |
 * | Card           | Form sections, step containers, results display     |
 * | LoadingSpinner | Submit loading state, data fetching indicators      |
 * | ErrorMessage   | API error display with retry functionality          |
 * 
 * ============================================================================
 * IMPORT EXAMPLES
 * ============================================================================
 * 
 * @example
 * // From pages (relative import)
 * import { Button, Input, Select, Card } from '../../components';
 * 
 * @example
 * // With path alias (if configured in tsconfig)
 * import { Button, Card, LoadingSpinner, ErrorMessage } from '@/components';
 * 
 * ============================================================================
 * FORM PAGE INTEGRATION EXAMPLE
 * ============================================================================
 * 
 * @example
 * // Complete form section example
 * import { Button, Input, Select, Card, LoadingSpinner, ErrorMessage } from '../../components';
 * 
 * function DemographicsForm({ onSubmit, isLoading, error }) {
 *   return (
 *     <Card title="Step 1: Demographics">
 *       <div className="space-y-4">
 *         <Input
 *           label="Age"
 *           type="number"
 *           min={1}
 *           max={120}
 *           value={age}
 *           onChange={(e) => setAge(e.target.value)}
 *         />
 *         
 *         <Select
 *           label="Gender"
 *           value={gender}
 *           onChange={(e) => setGender(e.target.value)}
 *           options={[
 *             { value: 'male', label: 'Male' },
 *             { value: 'female', label: 'Female' },
 *           ]}
 *         />
 *         
 *         {error && (
 *           <ErrorMessage message={error} onRetry={onSubmit} />
 *         )}
 *         
 *         <Button
 *           variant="primary"
 *           onClick={onSubmit}
 *           isLoading={isLoading}
 *           disabled={isLoading}
 *         >
 *           {isLoading ? 'Processing...' : 'Next Step →'}
 *         </Button>
 *       </div>
 *     </Card>
 *   );
 * }
 * 
 * ============================================================================
 * DESIGN TOKENS
 * ============================================================================
 * 
 * All components use consistent dark theme colors:
 * - Background: slate-800, slate-900
 * - Text: slate-100, slate-300, slate-400
 * - Borders: slate-600, slate-700
 * - Primary accent: cyan-500, cyan-600
 * - Error: red-400, red-500
 * - Success: green-400, green-500
 */

// ============================================================================
// FORM COMPONENTS
// ============================================================================

export { Button } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './Button';

export { Input } from './Input';
export type { InputProps } from './Input';

export { Select } from './Select';
export type { SelectProps, SelectOption } from './Select';

// ============================================================================
// LAYOUT COMPONENTS
// ============================================================================

export { Card } from './Card';
export type { CardProps, CardVariant } from './Card';

// ============================================================================
// FEEDBACK COMPONENTS
// ============================================================================

export { LoadingSpinner } from './LoadingSpinner';
export type { LoadingSpinnerProps, SpinnerSize } from './LoadingSpinner';

export { ErrorMessage } from './ErrorMessage';
export type { ErrorMessageProps } from './ErrorMessage';
