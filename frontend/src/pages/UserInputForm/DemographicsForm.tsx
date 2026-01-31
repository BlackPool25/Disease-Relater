/**
 * DemographicsForm Component
 * 
 * Step 1 of the risk calculator - collects age, gender, height, weight.
 * Calculates and displays BMI with classification.
 */
import type { DemographicsData } from '../../hooks/useFormState';
import './UserInputForm.css';

interface DemographicsFormProps {
  data: DemographicsData;
  onChange: (data: Partial<DemographicsData>) => void;
  bmi: number;
}

/**
 * Get BMI classification and color
 */
function getBMIClass(bmi: number): { label: string; color: string } {
  if (bmi === 0) return { label: '-', color: 'var(--color-neutral)' };
  if (bmi < 18.5) return { label: 'Underweight', color: 'var(--color-warning)' };
  if (bmi < 25) return { label: 'Normal', color: 'var(--color-success)' };
  if (bmi < 30) return { label: 'Overweight', color: 'var(--color-warning)' };
  return { label: 'Obese', color: 'var(--color-danger)' };
}

export function DemographicsForm({ data, onChange, bmi }: DemographicsFormProps) {
  const bmiClass = getBMIClass(bmi);

  return (
    <div className="form-section">
      <div className="form-section-header">
        <span className="step-badge">01</span>
        <div>
          <h2 className="form-section-title">Demographics</h2>
          <p className="form-section-subtitle">Basic information for risk stratification</p>
        </div>
      </div>

      <div className="form-grid">
        {/* Age */}
        <div className="form-field">
          <label className="form-label" htmlFor="age">
            Age
            <span className="form-hint">years</span>
          </label>
          <input
            id="age"
            type="number"
            className="form-input"
            min={1}
            max={120}
            value={data.age}
            onChange={(e) => onChange({ age: e.target.value ? Number(e.target.value) : '' })}
            placeholder="Enter age"
          />
        </div>

        {/* Gender */}
        <div className="form-field">
          <label className="form-label" htmlFor="gender">
            Biological Sex
            <span className="form-hint">for prevalence data</span>
          </label>
          <div className="radio-group">
            <label className={`radio-option ${data.gender === 'male' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="gender"
                value="male"
                checked={data.gender === 'male'}
                onChange={() => onChange({ gender: 'male' })}
              />
              <span className="radio-label">Male</span>
            </label>
            <label className={`radio-option ${data.gender === 'female' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="gender"
                value="female"
                checked={data.gender === 'female'}
                onChange={() => onChange({ gender: 'female' })}
              />
              <span className="radio-label">Female</span>
            </label>
          </div>
        </div>

        {/* Height */}
        <div className="form-field">
          <label className="form-label" htmlFor="height">
            Height
            {data.heightUnit === 'ft' && (
              <span className="form-hint">Enter as decimal (5'10" = 5.83)</span>
            )}
          </label>
          <div className="input-with-unit">
            <input
              id="height"
              type="number"
              step="0.01"
              className="form-input"
              min={1}
              value={data.height}
              onChange={(e) => onChange({ height: e.target.value ? Number(e.target.value) : '' })}
              placeholder={data.heightUnit === 'cm' ? '175' : '5.83'}
            />
            <select
              className="unit-select"
              value={data.heightUnit}
              onChange={(e) => onChange({ heightUnit: e.target.value as 'cm' | 'ft' })}
            >
              <option value="cm">cm</option>
              <option value="ft">ft</option>
            </select>
          </div>
        </div>

        {/* Weight */}
        <div className="form-field">
          <label className="form-label" htmlFor="weight">
            Weight
          </label>
          <div className="input-with-unit">
            <input
              id="weight"
              type="number"
              className="form-input"
              min={1}
              value={data.weight}
              onChange={(e) => onChange({ weight: e.target.value ? Number(e.target.value) : '' })}
              placeholder={data.weightUnit === 'kg' ? '70' : '154'}
            />
            <select
              className="unit-select"
              value={data.weightUnit}
              onChange={(e) => onChange({ weightUnit: e.target.value as 'kg' | 'lbs' })}
            >
              <option value="kg">kg</option>
              <option value="lbs">lbs</option>
            </select>
          </div>
        </div>
      </div>

      {/* BMI Display */}
      <div className="bmi-display">
        <div className="bmi-value-container">
          <span className="bmi-label">Body Mass Index</span>
          <span className="bmi-value" style={{ color: bmiClass.color }}>
            {bmi > 0 ? bmi.toFixed(1) : '-'}
          </span>
          <span className="bmi-classification" style={{ color: bmiClass.color }}>
            {bmiClass.label}
          </span>
        </div>
        <div className="bmi-scale">
          <div className="bmi-scale-segment" style={{ background: 'var(--color-warning)', flex: 18.5 }} />
          <div className="bmi-scale-segment" style={{ background: 'var(--color-success)', flex: 6.5 }} />
          <div className="bmi-scale-segment" style={{ background: 'var(--color-warning)', flex: 5 }} />
          <div className="bmi-scale-segment" style={{ background: 'var(--color-danger)', flex: 10 }} />
          {bmi > 0 && (
            <div
              className="bmi-indicator"
              style={{ left: `${Math.min(100, Math.max(0, ((bmi - 15) / 25) * 100))}%` }}
            />
          )}
        </div>
        <div className="bmi-scale-labels">
          <span>15</span>
          <span>18.5</span>
          <span>25</span>
          <span>30</span>
          <span>40</span>
        </div>
      </div>
    </div>
  );
}
