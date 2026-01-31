/**
 * UserInputForm - Multi-step Form Container
 * 
 * Parent component for the risk calculator form.
 * Manages step navigation, API submission, and results display.
 */
import { useState } from 'react';
import { AxiosError } from 'axios';
import { useFormState, FORM_STEPS } from '../../hooks/useFormState';
import { calculateRisk, type RiskCalculationResponse, getRiskLevelColor, formatRiskPercentage } from '../../api/calculate';
import { DemographicsForm } from './DemographicsForm';
import { HealthStatusForm } from './HealthStatusForm';
import { LifestyleForm } from './LifestyleForm';
import './UserInputForm.css';

export function UserInputForm() {
  const {
    formData,
    currentStep,
    totalSteps,
    updateDemographics,
    updateHealthStatus,
    updateLifestyle,
    nextStep,
    prevStep,
    goToStep,
    resetForm,
    isCurrentStepValid,
    calculateBMI,
  } = useFormState();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RiskCalculationResponse | null>(null);

  // Handle form submission
  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { demographics, healthStatus, lifestyle } = formData;

      const response = await calculateRisk({
        age: Number(demographics.age),
        gender: demographics.gender as 'male' | 'female',
        bmi: calculateBMI(),
        existing_conditions: healthStatus.existingConditions,
        exercise_level: lifestyle.exerciseLevel as 'sedentary' | 'light' | 'moderate' | 'active',
        smoking: lifestyle.smokingStatus === 'current',
      });

      setResult(response);
    } catch (err) {
      // Extract error message from various possible response formats
      const axiosError = err as AxiosError<{ 
        error?: { message?: string }; 
        detail?: string;
        message?: string;
      }>;
      
      const message = 
        axiosError.response?.data?.error?.message ||  // Backend error format
        axiosError.response?.data?.detail ||          // FastAPI validation format
        axiosError.response?.data?.message ||         // Alternative format
        (err instanceof Error ? err.message : 'Failed to calculate risk. Please try again.');
      
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Reset to form
  const handleReset = () => {
    setResult(null);
    setError(null);
    resetForm();
  };

  // Show results if available
  if (result) {
    return (
      <div className="form-container">
        <div className="results-container">
          <div className="results-header">
            <h2 className="results-title">Risk Analysis Complete</h2>
            <p className="results-subtitle">
              Based on {result.total_conditions_analyzed} conditions analyzed
            </p>
          </div>

          {/* Top risks */}
          <div className="risk-cards">
            {result.risk_scores.slice(0, 5).map((score, index) => (
              <div
                key={score.disease_id}
                className="risk-card"
                style={{ '--risk-color': getRiskLevelColor(score.level) } as React.CSSProperties}
              >
                <div className="risk-card-rank">#{index + 1}</div>
                <div className="risk-card-content">
                  <div className="risk-card-header">
                    <span className="risk-card-name">{score.disease_name}</span>
                    <span className="risk-card-code">{score.disease_id}</span>
                  </div>
                  <div className="risk-bar-container">
                    <div
                      className="risk-bar"
                      style={{ width: `${score.risk * 100}%` }}
                    />
                  </div>
                  <div className="risk-card-footer">
                    <span className="risk-percentage">{formatRiskPercentage(score.risk)}</span>
                    <span className={`risk-level ${score.level}`}>{score.level.replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* User position */}
          <div className="position-card">
            <h3>Your Position in Disease Space</h3>
            <div className="position-coords">
              <span>X: {result.user_position.x.toFixed(3)}</span>
              <span>Y: {result.user_position.y.toFixed(3)}</span>
              <span>Z: {result.user_position.z.toFixed(3)}</span>
            </div>
            <p className="position-hint">
              This position represents your health profile in 3D disease network space
            </p>
          </div>

          {/* Actions */}
          <div className="results-actions">
            <button className="btn btn-secondary" onClick={handleReset}>
              Calculate Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="form-container">
      {/* Progress indicator */}
      <div className="progress-container">
        <div className="progress-steps">
          {FORM_STEPS.map((step, index) => (
            <button
              key={step}
              className={`progress-step ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
              onClick={() => index < currentStep && goToStep(index)}
              disabled={index > currentStep}
            >
              <span className="progress-step-number">{index + 1}</span>
              <span className="progress-step-label">{step}</span>
            </button>
          ))}
        </div>
        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
          />
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Form steps */}
      <div className="form-content">
        {currentStep === 0 && (
          <DemographicsForm
            data={formData.demographics}
            onChange={updateDemographics}
            bmi={calculateBMI()}
          />
        )}
        {currentStep === 1 && (
          <HealthStatusForm
            data={formData.healthStatus}
            onChange={updateHealthStatus}
          />
        )}
        {currentStep === 2 && (
          <LifestyleForm
            data={formData.lifestyle}
            onChange={updateLifestyle}
          />
        )}
      </div>

      {/* Navigation */}
      <div className="form-navigation">
        <button
          className="btn btn-secondary"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          ← Previous
        </button>

        {currentStep < totalSteps - 1 ? (
          <button
            className="btn btn-primary"
            onClick={nextStep}
            disabled={!isCurrentStepValid}
          >
            Next →
          </button>
        ) : (
          <button
            className="btn btn-primary btn-submit"
            onClick={handleSubmit}
            disabled={!isCurrentStepValid || isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                Calculating...
              </>
            ) : (
              'Calculate Risk'
            )}
          </button>
        )}
      </div>
    </div>
  );
}
