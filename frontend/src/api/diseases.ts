/**
 * Diseases API Functions
 * 
 * Functions for fetching disease data from the backend.
 * Used for populating condition selection dropdowns.
 */
import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

/**
 * Disease record from the diseases endpoint
 */
export interface Disease {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  chapter_name: string | null;
  prevalence_male: number;
  prevalence_female: number;
  prevalence_total: number | null;
  vector_x: number | null;
  vector_y: number | null;
  vector_z: number | null;
}

/**
 * ICD-10 chapter for grouping diseases
 */
export interface IcdChapter {
  chapter_code: string;
  chapter_name: string;
  chapter_number: number | null;
  description: string | null;
}

/**
 * Paginated diseases response
 */
export interface DiseasesResponse {
  diseases: Disease[];
  total: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch paginated list of diseases
 * 
 * @param params - Query parameters for filtering and pagination
 * @returns List of diseases with total count
 */
export async function getDiseases(params?: {
  chapter?: string;
  limit?: number;
  offset?: number;
}): Promise<DiseasesResponse> {
  const response = await apiClient.get<DiseasesResponse>('/diseases', { params });
  return response.data;
}

/**
 * Fetch a single disease by ICD code
 * 
 * @param icdCode - ICD-10 code (e.g., 'E11', 'I10')
 * @returns Disease details or null if not found
 */
export async function getDiseaseByCode(icdCode: string): Promise<Disease | null> {
  try {
    const response = await apiClient.get<Disease>(`/diseases/${icdCode}`);
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Search diseases by name or ICD code
 * 
 * @param term - Search term
 * @param limit - Max results to return
 * @returns Matching diseases
 */
export async function searchDiseases(term: string, limit = 20): Promise<Disease[]> {
  const response = await apiClient.get<{ diseases: Disease[] }>(`/diseases/search/${encodeURIComponent(term)}`, {
    params: { limit },
  });
  return response.data.diseases || [];
}

/**
 * Fetch all ICD chapters
 * 
 * @returns List of ICD-10 chapters
 */
export async function getChapters(): Promise<IcdChapter[]> {
  const response = await apiClient.get<{ chapters: IcdChapter[] }>('/chapters');
  return response.data.chapters || [];
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Common conditions for quick selection in forms
 * Grouped by category with ICD codes
 */
export const COMMON_CONDITIONS = {
  cardiovascular: [
    { code: 'I10', label: 'Hypertension (High Blood Pressure)' },
    { code: 'I25', label: 'Chronic Ischaemic Heart Disease' },
    { code: 'I50', label: 'Heart Failure' },
    { code: 'I48', label: 'Atrial Fibrillation' },
    { code: 'I21', label: 'Acute Myocardial Infarction' },
  ],
  metabolic: [
    { code: 'E11', label: 'Type 2 Diabetes' },
    { code: 'E10', label: 'Type 1 Diabetes' },
    { code: 'E78', label: 'High Cholesterol' },
    { code: 'E66', label: 'Obesity' },
    { code: 'E03', label: 'Hypothyroidism' },
  ],
  respiratory: [
    { code: 'J45', label: 'Asthma' },
    { code: 'J44', label: 'COPD' },
    { code: 'J18', label: 'Pneumonia' },
  ],
  mental: [
    { code: 'F32', label: 'Depression' },
    { code: 'F41', label: 'Anxiety Disorder' },
    { code: 'F10', label: 'Alcohol Use Disorder' },
  ],
  musculoskeletal: [
    { code: 'M54', label: 'Back Pain' },
    { code: 'M17', label: 'Knee Osteoarthritis' },
    { code: 'M81', label: 'Osteoporosis' },
  ],
} as const;

/**
 * Get display name for a condition code
 */
export function getConditionLabel(code: string): string {
  for (const category of Object.values(COMMON_CONDITIONS)) {
    const found = category.find(c => c.code === code);
    if (found) return found.label;
  }
  return code;
}

/**
 * Validate that ICD codes exist in the database
 * Call this on app startup or before form submission
 * 
 * @param codes - Array of ICD-10 codes to validate
 * @returns Object with valid and invalid code arrays
 */
export async function validateConditionCodes(codes: string[]): Promise<{
  valid: string[];
  invalid: string[];
}> {
  const valid: string[] = [];
  const invalid: string[] = [];
  
  for (const code of codes) {
    const disease = await getDiseaseByCode(code);
    if (disease) {
      valid.push(code);
    } else {
      invalid.push(code);
    }
  }
  
  return { valid, invalid };
}
