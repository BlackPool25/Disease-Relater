/**
 * LifestyleForm Component
 * 
 * Step 3 of the risk calculator - collects lifestyle factors.
 * Exercise level, smoking status, and alcohol consumption.
 */
import type { LifestyleData } from '../../hooks/useFormState';
import './UserInputForm.css';

interface LifestyleFormProps {
  data: LifestyleData;
  onChange: (data: Partial<LifestyleData>) => void;
}

const EXERCISE_OPTIONS = [
  { value: 'sedentary', label: 'Sedentary', description: 'Little to no exercise', icon: '🪑' },
  { value: 'light', label: 'Light', description: '1-2 days per week', icon: '🚶' },
  { value: 'moderate', label: 'Moderate', description: '3-5 days per week', icon: '🏃' },
  { value: 'active', label: 'Active', description: '6-7 days per week', icon: '💪' },
] as const;

const SMOKING_OPTIONS = [
  { value: 'never', label: 'Never Smoked', icon: '🚭' },
  { value: 'former', label: 'Former Smoker', icon: '🔄' },
  { value: 'current', label: 'Current Smoker', icon: '🚬' },
] as const;

const ALCOHOL_OPTIONS = [
  { value: 'none', label: 'None', description: 'No alcohol' },
  { value: 'occasional', label: 'Occasional', description: '1-3 drinks/week' },
  { value: 'moderate', label: 'Moderate', description: '4-14 drinks/week' },
  { value: 'heavy', label: 'Heavy', description: '14+ drinks/week' },
] as const;

export function LifestyleForm({ data, onChange }: LifestyleFormProps) {
  return (
    <div className="form-section">
      <div className="form-section-header">
        <span className="step-badge">03</span>
        <div>
          <h2 className="form-section-title">Lifestyle Factors</h2>
          <p className="form-section-subtitle">Activity and habits that affect disease risk</p>
        </div>
      </div>

      {/* Exercise Level */}
      <div className="lifestyle-group">
        <h3 className="lifestyle-group-title">Physical Activity Level</h3>
        <div className="option-cards">
          {EXERCISE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`option-card ${data.exerciseLevel === option.value ? 'selected' : ''}`}
              onClick={() => onChange({ exerciseLevel: option.value })}
            >
              <span className="option-icon">{option.icon}</span>
              <span className="option-label">{option.label}</span>
              <span className="option-description">{option.description}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Smoking Status */}
      <div className="lifestyle-group">
        <h3 className="lifestyle-group-title">Smoking Status</h3>
        <div className="option-cards horizontal">
          {SMOKING_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`option-card compact ${data.smokingStatus === option.value ? 'selected' : ''}`}
              onClick={() => onChange({ smokingStatus: option.value })}
            >
              <span className="option-icon">{option.icon}</span>
              <span className="option-label">{option.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Alcohol Consumption */}
      <div className="lifestyle-group">
        <h3 className="lifestyle-group-title">
          Alcohol Consumption
          <span className="optional-badge">Optional</span>
        </h3>
        <div className="alcohol-slider-container">
          <div className="alcohol-options">
            {ALCOHOL_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`alcohol-option ${data.alcoholConsumption === option.value ? 'selected' : ''}`}
                onClick={() => onChange({ alcoholConsumption: option.value })}
              >
                <span className="alcohol-label">{option.label}</span>
                <span className="alcohol-description">{option.description}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="lifestyle-summary">
        <div className="summary-item">
          <span className="summary-label">Exercise</span>
          <span className="summary-value">
            {EXERCISE_OPTIONS.find((o) => o.value === data.exerciseLevel)?.label || 'Not selected'}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Smoking</span>
          <span className={`summary-value ${data.smokingStatus === 'current' ? 'warning' : ''}`}>
            {SMOKING_OPTIONS.find((o) => o.value === data.smokingStatus)?.label || 'Not selected'}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Alcohol</span>
          <span className={`summary-value ${data.alcoholConsumption === 'heavy' ? 'warning' : ''}`}>
            {ALCOHOL_OPTIONS.find((o) => o.value === data.alcoholConsumption)?.label || 'Not selected'}
          </span>
        </div>
      </div>
    </div>
  );
}
