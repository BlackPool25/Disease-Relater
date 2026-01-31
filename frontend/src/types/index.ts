/**
 * TypeScript Types for Disease Visualizer Frontend
 * 
 * Adapted from api/types.ts for frontend use.
 * Provides type definitions for API responses and component props.
 */

// =============================================================================
// CORE ENUMS
// =============================================================================

/** Granularity levels for disease classification */
export type Granularity = 'ICD' | 'Blocks' | 'Chronic';

/** Sex/gender categories for stratification */
export type Sex = 'Male' | 'Female' | 'All';

/** Relationship strength classification based on odds ratio */
export type RelationshipStrength = 'extreme' | 'very_strong' | 'strong' | 'moderate' | 'weak';

/** Risk level classification for display */
export type RiskLevel = 'very_high' | 'high' | 'moderate' | 'low';

/** Exercise level options */
export type ExerciseLevel = 'sedentary' | 'light' | 'moderate' | 'active';


// =============================================================================
// DISEASE ENTITIES
// =============================================================================

/**
 * Disease record from the database
 */
export interface Disease {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  granularity: Granularity | null;
  prevalence_male: number | null;
  prevalence_female: number | null;
  prevalence_total: number | null;
  /** X coordinate from 3D UMAP embedding */
  vector_x: number | null;
  /** Y coordinate from 3D UMAP embedding */
  vector_y: number | null;
  /** Z coordinate from 3D UMAP embedding */
  vector_z: number | null;
  has_english_name: boolean | null;
  has_german_name: boolean | null;
  has_prevalence_data: boolean | null;
  has_3d_coordinates: boolean | null;
}

/**
 * Disease with chapter name included
 */
export interface DiseaseComplete extends Disease {
  chapter_name: string | null;
}

/**
 * Related disease with relationship details
 */
export interface RelatedDisease {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  odds_ratio: number;
  p_value: number | null;
  patient_count_total: number | null;
  relationship_strength: RelationshipStrength | null;
}


// =============================================================================
// DISEASE RELATIONSHIPS
// =============================================================================

/**
 * Aggregated comorbidity relationship between two diseases
 */
export interface DiseaseRelationship {
  id: number;
  disease_1_id: number;
  disease_2_id: number;
  /** Average odds ratio - higher = stronger association */
  odds_ratio: number;
  p_value: number | null;
  patient_count_total: number | null;
  icd_chapter_1: string | null;
  icd_chapter_2: string | null;
  relationship_strength: RelationshipStrength | null;
}


// =============================================================================
// NETWORK DATA (for 3D visualization)
// =============================================================================

/**
 * Node in the 3D disease network
 */
export interface NetworkNode {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  vector_x: number | null;
  vector_y: number | null;
  vector_z: number | null;
  prevalence_total: number | null;
}

/**
 * Edge in the 3D disease network
 */
export interface NetworkEdge {
  disease_1_id: number;
  disease_1_code: string;
  disease_1_name: string | null;
  disease_2_id: number;
  disease_2_code: string;
  disease_2_name: string | null;
  odds_ratio: number;
  p_value: number | null;
  relationship_strength: string | null;
  patient_count_total: number | null;
}

/**
 * Complete network data for visualization
 */
export interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  metadata: {
    min_odds_ratio: number;
    chapter_filter?: string;
    total_nodes: number;
    total_edges: number;
  };
}


// =============================================================================
// RISK CALCULATOR
// =============================================================================

/**
 * Request body for risk calculation endpoint
 */
export interface RiskCalculationRequest {
  age: number;
  gender: 'male' | 'female';
  bmi: number;
  existing_conditions: string[];
  exercise_level: ExerciseLevel;
  smoking: boolean;
}

/**
 * Individual risk score for a disease
 */
export interface RiskScore {
  disease_id: string;
  disease_name: string | null;
  risk: number;
  level: RiskLevel;
  contributing_factors: string[];
}

/**
 * Pull vector pointing toward high-risk diseases
 */
export interface PullVector {
  disease_id: string;
  disease_name: string | null;
  risk: number;
  vector_x: number;
  vector_y: number;
  vector_z: number;
  magnitude: number;
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
 * Response from risk calculation endpoint
 */
export interface RiskCalculationResponse {
  risk_scores: RiskScore[];
  user_position: UserPosition;
  pull_vectors: PullVector[];
  total_conditions_analyzed: number;
  analysis_metadata: {
    conditions_processed: string[];
    related_diseases_found: number;
    gender: string;
    age: number;
  };
}


// =============================================================================
// ICD CHAPTERS
// =============================================================================

/**
 * ICD-10 chapter lookup
 */
export interface IcdChapter {
  chapter_code: string;
  chapter_name: string;
  chapter_number: number | null;
  description: string | null;
}

/**
 * Chapter statistics
 */
export interface ChapterStatistics {
  chapter_code: string;
  chapter_name: string;
  disease_count: number;
  avg_prevalence: number | null;
  with_3d: number;
}


// =============================================================================
// API RESPONSES
// =============================================================================

/**
 * Standard API error response
 */
export interface ApiError {
  message: string;
  code: number;
  hint?: string;
  details?: string;
}

/**
 * Search result
 */
export interface SearchResult {
  id: number;
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  chapter_name: string | null;
  prevalence_total: number | null;
}


// =============================================================================
// CONSTANTS
// =============================================================================

/** ICD-10 chapter codes to names */
export const ICD_CHAPTERS: Record<string, string> = {
  'I': 'Infectious and parasitic diseases',
  'II': 'Neoplasms',
  'III': 'Blood and immune disorders',
  'IV': 'Endocrine, nutritional and metabolic',
  'V': 'Mental and behavioral disorders',
  'VI': 'Nervous system',
  'VII': 'Eye and adnexa',
  'VIII': 'Ear and mastoid process',
  'IX': 'Circulatory system',
  'X': 'Respiratory system',
  'XI': 'Digestive system',
  'XII': 'Skin and subcutaneous tissue',
  'XIII': 'Musculoskeletal and connective tissue',
  'XIV': 'Genitourinary system',
  'XV': 'Pregnancy and childbirth',
  'XVI': 'Perinatal conditions',
  'XVII': 'Congenital malformations',
  'XVIII': 'Symptoms and abnormal findings',
  'XIX': 'Injury, poisoning and external causes',
  'XX': 'External causes of morbidity',
  'XXI': 'Factors influencing health status',
};

/** Odds ratio thresholds for relationship strength */
export const RELATIONSHIP_STRENGTH_THRESHOLDS = {
  extreme: 50,
  very_strong: 10,
  strong: 5,
  moderate: 2,
  weak: 0,
} as const;

/** Risk score thresholds for risk levels */
export const RISK_LEVEL_THRESHOLDS = {
  very_high: 0.75,
  high: 0.5,
  moderate: 0.25,
  low: 0,
} as const;


// =============================================================================
// TYPE GUARDS
// =============================================================================

/** Check if an object is a Disease */
export function isDisease(obj: unknown): obj is Disease {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'icd_code' in obj
  );
}

/** Check if a string is a valid RelationshipStrength */
export function isRelationshipStrength(str: string): str is RelationshipStrength {
  return ['extreme', 'very_strong', 'strong', 'moderate', 'weak'].includes(str);
}

/** Check if a string is a valid Granularity */
export function isGranularity(str: string): str is Granularity {
  return ['ICD', 'Blocks', 'Chronic'].includes(str);
}

/** Check if a string is a valid Sex */
export function isSex(str: string): str is Sex {
  return ['Male', 'Female', 'All'].includes(str);
}

/** Check if a string is a valid RiskLevel */
export function isRiskLevel(str: string): str is RiskLevel {
  return ['very_high', 'high', 'moderate', 'low'].includes(str);
}


// =============================================================================
// UTILITY TYPES
// =============================================================================

/** Make all properties nullable */
export type Nullable<T> = { [K in keyof T]: T[K] | null };

/** Extract ICD code from Disease */
export type IcdCode = Disease['icd_code'];

/** 3D Vector type for Three.js */
export type Vector3D = [number, number, number];
