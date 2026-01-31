/**
 * useFormState Hook
 * 
 * Multi-step form state management for the risk calculator.
 * Manages form data across Demographics, Health Status, and Lifestyle steps.
 * Includes localStorage persistence to save form drafts.
 */
import { useState, useCallback, useEffect } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface DemographicsData {
  age: number | '';
  gender: 'male' | 'female' | '';
  height: number | '';
  weight: number | '';
  heightUnit: 'cm' | 'ft';
  weightUnit: 'kg' | 'lbs';
}

export interface HealthStatusData {
  existingConditions: string[];
}

export interface LifestyleData {
  exerciseLevel: 'sedentary' | 'light' | 'moderate' | 'active' | '';
  smokingStatus: 'never' | 'former' | 'current' | '';
  alcoholConsumption: 'none' | 'occasional' | 'moderate' | 'heavy' | '';
}

export interface FormState {
  demographics: DemographicsData;
  healthStatus: HealthStatusData;
  lifestyle: LifestyleData;
}

// ============================================================================
// Initial State
// ============================================================================

const initialDemographics: DemographicsData = {
  age: '',
  gender: '',
  height: '',
  weight: '',
  heightUnit: 'cm',
  weightUnit: 'kg',
};

const initialHealthStatus: HealthStatusData = {
  existingConditions: [],
};

const initialLifestyle: LifestyleData = {
  exerciseLevel: '',
  smokingStatus: '',
  alcoholConsumption: '',
};

const initialState: FormState = {
  demographics: initialDemographics,
  healthStatus: initialHealthStatus,
  lifestyle: initialLifestyle,
};

const STORAGE_KEY = 'disease-risk-form-draft';

// ============================================================================
// Hook
// ============================================================================

export const FORM_STEPS = ['Demographics', 'Health Status', 'Lifestyle'] as const;
export type FormStep = (typeof FORM_STEPS)[number];

/**
 * Multi-step form state management hook
 * 
 * @returns Form state, updaters, navigation, and utility functions
 * 
 * @example
 * const { formData, currentStep, updateDemographics, nextStep } = useFormState();
 */
export function useFormState() {
  // Load from localStorage on init
  const [formData, setFormData] = useState<FormState>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Merge with initial state to handle any new fields
        return {
          demographics: { ...initialDemographics, ...parsed.demographics },
          healthStatus: { ...initialHealthStatus, ...parsed.healthStatus },
          lifestyle: { ...initialLifestyle, ...parsed.lifestyle },
        };
      }
    } catch {
      // Ignore invalid JSON in localStorage
    }
    return initialState;
  });
  const [currentStep, setCurrentStep] = useState(0);

  // Save to localStorage whenever form data changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(formData));
    } catch {
      // Ignore storage errors (e.g., quota exceeded)
    }
  }, [formData]);

  // Update functions for each section
  const updateDemographics = useCallback((data: Partial<DemographicsData>) => {
    setFormData((prev) => ({
      ...prev,
      demographics: { ...prev.demographics, ...data },
    }));
  }, []);

  const updateHealthStatus = useCallback((data: Partial<HealthStatusData>) => {
    setFormData((prev) => ({
      ...prev,
      healthStatus: { ...prev.healthStatus, ...data },
    }));
  }, []);

  const updateLifestyle = useCallback((data: Partial<LifestyleData>) => {
    setFormData((prev) => ({
      ...prev,
      lifestyle: { ...prev.lifestyle, ...data },
    }));
  }, []);

  // Navigation
  const nextStep = useCallback(() => {
    setCurrentStep((s) => Math.min(s + 1, FORM_STEPS.length - 1));
  }, []);

  const prevStep = useCallback(() => {
    setCurrentStep((s) => Math.max(s - 1, 0));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step < FORM_STEPS.length) {
      setCurrentStep(step);
    }
  }, []);

  const resetForm = useCallback(() => {
    setFormData(initialState);
    setCurrentStep(0);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Validation
  const isStepValid = useCallback((step: number): boolean => {
    switch (step) {
      case 0: // Demographics
        const d = formData.demographics;
        return (
          d.age !== '' && d.age > 0 && d.age <= 120 &&
          d.gender !== '' &&
          d.height !== '' && d.height > 0 &&
          d.weight !== '' && d.weight > 0
        );
      case 1: // Health Status
        return formData.healthStatus.existingConditions.length > 0;
      case 2: // Lifestyle
        const l = formData.lifestyle;
        return l.exerciseLevel !== '' && l.smokingStatus !== '';
      default:
        return false;
    }
  }, [formData]);

  const isCurrentStepValid = isStepValid(currentStep);

  // BMI Calculation
  const calculateBMI = useCallback((): number => {
    const { height, weight, heightUnit, weightUnit } = formData.demographics;
    if (!height || !weight) return 0;

    // Convert to metric
    const heightM = heightUnit === 'cm' 
      ? Number(height) / 100 
      : Number(height) * 0.3048; // ft to m
    const weightKg = weightUnit === 'kg' 
      ? Number(weight) 
      : Number(weight) * 0.453592; // lbs to kg

    if (heightM <= 0) return 0;
    return weightKg / (heightM * heightM);
  }, [formData.demographics]);

  return {
    // State
    formData,
    currentStep,
    currentStepName: FORM_STEPS[currentStep],
    totalSteps: FORM_STEPS.length,
    
    // Updaters
    updateDemographics,
    updateHealthStatus,
    updateLifestyle,
    
    // Navigation
    nextStep,
    prevStep,
    goToStep,
    resetForm,
    
    // Validation
    isStepValid,
    isCurrentStepValid,
    
    // Utilities
    calculateBMI,
  };
}

export type UseFormStateReturn = ReturnType<typeof useFormState>;
