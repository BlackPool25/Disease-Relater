/**
 * TypeScript Types for Disease-Relater API
 * 
 * Generated from Supabase database schema
 * Project: gbohehihcncmlcpyxomv
 * Date: 2026-01-30
 * 
 * Usage:
 * ```typescript
 * import { Database, Disease, DiseaseRelationship } from './types';
 * 
 * const disease: Disease = { ... };
 * ```
 */

// ============================================================================
// Core Types
// ============================================================================

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Granularity = 'ICD' | 'Blocks' | 'Chronic';
export type Sex = 'Male' | 'Female' | 'All';
export type RelationshipStrength = 'extreme' | 'very_strong' | 'strong' | 'moderate' | 'weak';

// ============================================================================
// Database Schema
// ============================================================================

export interface Database {
  public: {
    Tables: {
      diseases: {
        Row: Disease;
        Insert: Omit<Disease, 'id' | 'created_at' | 'updated_at'> & {
          id?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Disease>;
      };
      disease_relationships: {
        Row: DiseaseRelationship;
        Insert: Omit<DiseaseRelationship, 'id' | 'created_at'> & {
          id?: number;
          created_at?: string;
        };
        Update: Partial<DiseaseRelationship>;
      };
      disease_relationships_stratified: {
        Row: DiseaseRelationshipStratified;
        Insert: Omit<DiseaseRelationshipStratified, 'id' | 'created_at'> & {
          id?: number;
          created_at?: string;
        };
        Update: Partial<DiseaseRelationshipStratified>;
      };
      icd_chapters: {
        Row: IcdChapter;
        Insert: IcdChapter;
        Update: Partial<IcdChapter>;
      };
    };
    Views: {
      diseases_complete: DiseaseComplete;
      disease_network_stats: DiseaseNetworkStats;
      top_relationships: TopRelationship;
    };
  };
}

// ============================================================================
// Table Types
// ============================================================================

/**
 * Disease record from diseases table
 * Merges 736 diseases_master + 1,080 disease_vectors_3d
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
  /** X coordinate from 3D UMAP embedding for visualization */
  vector_x: number | null;
  /** Y coordinate from 3D UMAP embedding for visualization */
  vector_y: number | null;
  /** Z coordinate from 3D UMAP embedding for visualization */
  vector_z: number | null;
  has_english_name: boolean | null;
  has_german_name: boolean | null;
  has_prevalence_data: boolean | null;
  has_3d_coordinates: boolean | null;
  data_source: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Aggregated comorbidity relationship
 * 9,232 relationships from disease_relationships_master.csv
 */
export interface DiseaseRelationship {
  id: number;
  disease_1_id: number;
  disease_2_id: number;
  /** Average odds ratio across all strata - higher = stronger association */
  odds_ratio: number;
  /** Statistical significance - lower = more significant */
  p_value: number | null;
  patient_count_total: number | null;
  icd_chapter_1: string | null;
  icd_chapter_2: string | null;
  /** Auto-classified: extreme (>50), very_strong (>10), strong (>5), moderate (>2), weak (<2) */
  relationship_strength: RelationshipStrength | null;
  created_at: string | null;
}

/**
 * Stratified relationship with demographic details
 * 74,901 rows from disease_pairs_clean.csv
 */
export interface DiseaseRelationshipStratified {
  id: number;
  disease_1_id: number;
  disease_2_id: number;
  sex: Sex | null;
  age_group: string | null;
  year_range: string | null;
  odds_ratio: number;
  p_value: number | null;
  patient_count: number | null;
  disease_1_name_de: string | null;
  disease_1_name_en: string | null;
  disease_2_name_de: string | null;
  disease_2_name_en: string | null;
  icd_chapter_1: string | null;
  icd_chapter_2: string | null;
  granularity: Granularity | null;
  created_at: string | null;
}

/**
 * ICD-10 chapter lookup
 * 21 standard ICD-10 chapters
 */
export interface IcdChapter {
  chapter_code: string;
  chapter_name: string;
  chapter_number: number | null;
  description: string | null;
  created_at: string | null;
}

// ============================================================================
// View Types
// ============================================================================

/**
 * Complete disease view with chapter names
 * Convenience view joining diseases + icd_chapters
 */
export interface DiseaseComplete {
  id: number | null;
  icd_code: string | null;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  chapter_name: string | null;
  granularity: Granularity | null;
  prevalence_male: number | null;
  prevalence_female: number | null;
  prevalence_total: number | null;
  vector_x: number | null;
  vector_y: number | null;
  vector_z: number | null;
  has_english_name: boolean | null;
  has_german_name: boolean | null;
  has_prevalence_data: boolean | null;
  has_3d_coordinates: boolean | null;
}

/**
 * Disease network statistics view
 * Pre-computed connection counts and metrics
 */
export interface DiseaseNetworkStats {
  id: number | null;
  icd_code: string | null;
  name_english: string | null;
  chapter_code: string | null;
  connection_count: number | null;
  avg_odds_ratio: number | null;
  max_odds_ratio: number | null;
}

/**
 * Top relationships view with disease names
 * Convenience view for displaying top comorbidities
 */
export interface TopRelationship {
  id: number | null;
  disease_1_code: string | null;
  disease_1_name: string | null;
  disease_2_code: string | null;
  disease_2_name: string | null;
  odds_ratio: number | null;
  p_value: number | null;
  patient_count_total: number | null;
  relationship_strength: RelationshipStrength | null;
  icd_chapter_1: string | null;
  icd_chapter_2: string | null;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Query parameters for listing diseases
 */
export interface ListDiseasesParams {
  chapter_code?: string;
  limit?: number;
  offset?: number;
  order?: string;
  has_3d_coordinates?: boolean;
  has_prevalence_data?: boolean;
}

/**
 * Query parameters for getting related diseases
 */
export interface GetRelatedDiseasesParams {
  icd_code: string;
  limit?: number;
  min_odds_ratio?: number;
  bidirectional?: boolean;
}

/**
 * Query parameters for network data
 */
export interface GetNetworkDataParams {
  min_odds_ratio?: number;
  max_edges?: number;
  chapter_filter?: string;
}

/**
 * Query parameters for prevalence
 */
export interface GetPrevalenceParams {
  icd_code: string;
  sex?: Sex;
  age_group?: string;
}

/**
 * Search parameters
 */
export interface SearchDiseasesParams {
  search_term: string;
  limit?: number;
  search_in_names?: boolean;
  search_in_codes?: boolean;
}

// ============================================================================
// Response Types
// ============================================================================

/**
 * Network data response
 */
export interface NetworkData {
  nodes: Array<{
    id: number;
    icd_code: string;
    name_english: string | null;
    name_german: string | null;
    chapter_code: string | null;
    vector_x: number | null;
    vector_y: number | null;
    vector_z: number | null;
    prevalence_total: number | null;
  }>;
  edges: Array<{
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
  }>;
  metadata: {
    min_odds_ratio: number;
    chapter_filter?: string;
    total_nodes: number;
    total_edges: number;
  };
}

/**
 * Prevalence response
 */
export interface PrevalenceData {
  icd_code: string;
  name_english: string | null;
  name_german: string | null;
  chapter_code: string | null;
  prevalence: number | null;
  prevalence_male: number | null;
  prevalence_female: number | null;
  prevalence_total: number | null;
  stratified?: {
    age_group: string;
    avg_patient_count: number;
    relationship_count: number;
    avg_odds_ratio: number;
  };
}

/**
 * Database statistics response
 */
export interface DatabaseStatistics {
  diseases: {
    total_diseases: number;
    with_english_names: number;
    with_3d_coords: number;
    with_prevalence: number;
    avg_prevalence: number;
    chapters_count: number;
  };
  relationships_by_strength: Array<{
    relationship_strength: string;
    count: number;
    avg_odds_ratio: number;
  }>;
  database_status: string;
}

/**
 * Chapter statistics response
 */
export interface ChapterStatistics {
  chapter_code: string;
  chapter_name: string;
  disease_count: number;
  avg_prevalence: number | null;
  with_3d: number;
}

// ============================================================================
// API Error Types
// ============================================================================

export interface ApiError {
  message: string;
  code: number;
  hint?: string;
  details?: string;
}

// ============================================================================
// Helper Types
// ============================================================================

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
  has_english_name: boolean | null;
}

// ============================================================================
// Constants
// ============================================================================

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

export const RELATIONSHIP_STRENGTH_THRESHOLDS = {
  extreme: 50,
  very_strong: 10,
  strong: 5,
  moderate: 2,
  weak: 0,
} as const;

// ============================================================================
// Type Guards
// ============================================================================

export function isDisease(obj: unknown): obj is Disease {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'icd_code' in obj
  );
}

export function isDiseaseRelationship(obj: unknown): obj is DiseaseRelationship {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'disease_1_id' in obj &&
    'disease_2_id' in obj &&
    'odds_ratio' in obj
  );
}

export function isRelationshipStrength(str: string): str is RelationshipStrength {
  return ['extreme', 'very_strong', 'strong', 'moderate', 'weak'].includes(str);
}

export function isGranularity(str: string): str is Granularity {
  return ['ICD', 'Blocks', 'Chronic'].includes(str);
}

export function isSex(str: string): str is Sex {
  return ['Male', 'Female', 'All'].includes(str);
}
