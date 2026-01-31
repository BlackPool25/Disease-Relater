/**
 * Risk Calculation API Functions
 * 
 * Functions for calling the POST /api/calculate-risk endpoint.
 * Calculates personalized disease risk based on user health data.
 */
import { apiClient } from './client';

// ============================================================================
// Request Types
// ============================================================================

export type Gender = 'male' | 'female';
export type ExerciseLevel = 'sedentary' | 'light' | 'moderate' | 'active';

/**
 * Request body for risk calculation
 */
export interface RiskCalculationRequest {
  age: number;
  gender: Gender;
  bmi: number;
  existing_conditions: string[];
  exercise_level: ExerciseLevel;
  smoking: boolean;
}

// ============================================================================
// Response Types
// ============================================================================

export type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high';

/**
 * Individual disease risk score
 */
export interface RiskScore {
  disease_id: string;
  disease_name: string;
  risk: number;
  level: RiskLevel;
  contributing_factors: string[];
}

/**
 * User's position in 3D disease space
 */
export interface UserPosition {
  x: number;
  y: number;
  z: number;
}

/**
 * Directional vector toward a high-risk disease
 */
export interface PullVector {
  disease_id: string;
  disease_name: string;
  risk: number;
  vector_x: number;
  vector_y: number;
  vector_z: number;
  magnitude: number;
}

/**
 * Complete response from risk calculation endpoint
 */
export interface RiskCalculationResponse {
  risk_scores: RiskScore[];
  user_position: UserPosition;
  pull_vectors: PullVector[];
  total_conditions_analyzed: number;
  analysis_metadata: {
    conditions_processed: string[];
    related_diseases_analyzed: number;
    gender: string;
    age: number;
  };
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Calculate personalized disease risk scores
 * 
 * @param data - User health data including demographics and conditions
 * @returns Risk scores, user position in 3D space, and pull vectors
 * @throws AxiosError on network or validation errors
 * 
 * @example
 * const result = await calculateRisk({
 *   age: 45,
 *   gender: 'male',
 *   bmi: 28.5,
 *   existing_conditions: ['E11', 'I10'],
 *   exercise_level: 'moderate',
 *   smoking: false
 * });
 */
export async function calculateRisk(data: RiskCalculationRequest): Promise<RiskCalculationResponse> {
  const response = await apiClient.post<RiskCalculationResponse>('/calculate-risk', data);
  return response.data;
}

/**
 * Helper to get risk level color for UI display
 */
export function getRiskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'very_high': return '#dc2626'; // red-600
    case 'high': return '#ea580c'; // orange-600
    case 'moderate': return '#ca8a04'; // yellow-600
    case 'low': return '#16a34a'; // green-600
    default: return '#6b7280'; // gray-500
  }
}

/**
 * Helper to format risk score as percentage
 */
export function formatRiskPercentage(risk: number): string {
  return `${(risk * 100).toFixed(1)}%`;
}
