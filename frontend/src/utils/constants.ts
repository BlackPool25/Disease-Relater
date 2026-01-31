/**
 * Application Constants
 * 
 * Centralized configuration values for the Disease Visualizer frontend.
 */

// =============================================================================
// API CONFIGURATION
// =============================================================================

/** Base URL for API requests (from environment or default) */
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/** API endpoints */
export const API_ENDPOINTS = {
  // Health checks
  health: '/health',
  ready: '/ready',
  
  // Diseases
  diseases: '/diseases',
  diseaseById: (id: string | number) => `/diseases/${id}`,
  diseaseRelated: (id: string | number) => `/diseases/${id}/related`,
  diseaseSearch: (term: string) => `/diseases/search/${encodeURIComponent(term)}`,
  
  // Network data
  network: '/network',
  
  // Chapters
  chapters: '/chapters',
  
  // Risk calculator
  calculateRisk: '/calculate-risk',
} as const;


// =============================================================================
// UI CONFIGURATION
// =============================================================================

/** Default pagination settings */
export const PAGINATION = {
  defaultLimit: 50,
  maxLimit: 500,
} as const;

/** Debounce delays (ms) */
export const DEBOUNCE = {
  search: 300,
  resize: 150,
  scroll: 100,
} as const;

/** Animation durations (ms) */
export const ANIMATION = {
  fast: 150,
  normal: 300,
  slow: 500,
} as const;


// =============================================================================
// 3D VISUALIZATION
// =============================================================================

/** Default network visualization settings */
export const NETWORK_DEFAULTS = {
  minOddsRatio: 5.0,
  maxEdges: 1000,
} as const;

/** Camera defaults for Three.js */
export const CAMERA_DEFAULTS = {
  fov: 60,
  near: 0.1,
  far: 1000,
  position: [0, 0, 5] as [number, number, number],
} as const;


// =============================================================================
// LOCAL STORAGE KEYS
// =============================================================================

export const STORAGE_KEYS = {
  userPreferences: 'disease-viz-preferences',
  recentSearches: 'disease-viz-recent-searches',
  savedConditions: 'disease-viz-saved-conditions',
} as const;


// =============================================================================
// FORM VALIDATION
// =============================================================================

export const VALIDATION = {
  age: {
    min: 1,
    max: 120,
  },
  bmi: {
    min: 10,
    max: 60,
  },
  conditions: {
    min: 1,
    max: 50,
  },
  height: {
    cm: { min: 50, max: 250 },
    ft: { min: 1.5, max: 8.5 },  // Decimal feet
  },
  weight: {
    kg: { min: 20, max: 300 },
    lbs: { min: 44, max: 660 },
  },
} as const;
