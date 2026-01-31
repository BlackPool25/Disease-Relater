/**
 * Utility Helper Functions
 * 
 * Common utilities for the Disease Visualizer frontend.
 */

import type { RiskLevel, RelationshipStrength } from '../types';
import { RISK_LEVEL_THRESHOLDS } from '../types';

// =============================================================================
// FORMATTING
// =============================================================================

/**
 * Format a number as a percentage string
 */
export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number with fixed decimal places
 */
export function formatNumber(value: number, decimals = 2): string {
  return value.toFixed(decimals);
}

/**
 * Format odds ratio for display (e.g., "15.5x" or "2.3x")
 */
export function formatOddsRatio(oddsRatio: number): string {
  if (oddsRatio >= 100) return `${Math.round(oddsRatio)}x`;
  if (oddsRatio >= 10) return `${oddsRatio.toFixed(1)}x`;
  return `${oddsRatio.toFixed(2)}x`;
}

/**
 * Format a disease name for display (handles null/empty)
 */
export function formatDiseaseName(
  nameEnglish: string | null | undefined,
  nameGerman: string | null | undefined,
  icdCode: string
): string {
  if (nameEnglish && nameEnglish.trim()) return nameEnglish;
  if (nameGerman && nameGerman.trim()) return nameGerman;
  return icdCode;
}


// =============================================================================
// RISK CALCULATIONS
// =============================================================================

/**
 * Get risk level from score (0-1)
 */
export function getRiskLevel(score: number): RiskLevel {
  if (score >= RISK_LEVEL_THRESHOLDS.very_high) return 'very_high';
  if (score >= RISK_LEVEL_THRESHOLDS.high) return 'high';
  if (score >= RISK_LEVEL_THRESHOLDS.moderate) return 'moderate';
  return 'low';
}

/**
 * Get display label for risk level
 */
export function getRiskLevelLabel(level: RiskLevel): string {
  const labels: Record<RiskLevel, string> = {
    very_high: 'Very High',
    high: 'High',
    moderate: 'Moderate',
    low: 'Low',
  };
  return labels[level];
}

/**
 * Get display label for relationship strength
 */
export function getRelationshipStrengthLabel(strength: RelationshipStrength): string {
  const labels: Record<RelationshipStrength, string> = {
    extreme: 'Extreme',
    very_strong: 'Very Strong',
    strong: 'Strong',
    moderate: 'Moderate',
    weak: 'Weak',
  };
  return labels[strength];
}


// =============================================================================
// VALIDATION
// =============================================================================

/**
 * Validate ICD-10 code format (basic check)
 */
export function isValidIcdCode(code: string): boolean {
  // ICD-10 codes are 3-7 characters: letter + 2 digits + optional decimal + more digits
  return /^[A-Z]\d{2}(\.\d{1,4})?$/i.test(code);
}

/**
 * Clamp a number between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}


// =============================================================================
// 3D HELPERS
// =============================================================================

/**
 * Normalize coordinates to [-1, 1] range
 */
export function normalizeCoordinate(
  value: number,
  min: number,
  max: number
): number {
  if (max === min) return 0;
  return ((value - min) / (max - min)) * 2 - 1;
}

/**
 * Calculate distance between two 3D points
 */
export function distance3D(
  p1: [number, number, number],
  p2: [number, number, number]
): number {
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  const dz = p2[2] - p1[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

/**
 * Lerp (linear interpolation) between two values
 */
export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}


// =============================================================================
// DEBOUNCING & THROTTLING
// =============================================================================

/**
 * Debounce a function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  
  return function debounced(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func(...args);
    }, wait);
  };
}


// =============================================================================
// COLOR UTILITIES
// =============================================================================

/**
 * Convert hex color to RGB values (0-255)
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;
  return {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  };
}

/**
 * Convert RGB to hex color
 */
export function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => {
    const hex = Math.round(clamp(x, 0, 255)).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('');
}

/**
 * Blend two colors
 */
export function blendColors(color1: string, color2: string, ratio: number): string {
  const c1 = hexToRgb(color1);
  const c2 = hexToRgb(color2);
  if (!c1 || !c2) return color1;
  
  return rgbToHex(
    lerp(c1.r, c2.r, ratio),
    lerp(c1.g, c2.g, ratio),
    lerp(c1.b, c2.b, ratio)
  );
}


// =============================================================================
// MISC UTILITIES
// =============================================================================

/**
 * Generate a unique ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

/**
 * Sleep for a given duration (useful for animations)
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if running in browser environment
 */
export function isBrowser(): boolean {
  return typeof window !== 'undefined';
}


// =============================================================================
// UNIT CONVERSIONS
// =============================================================================

/**
 * Convert feet and inches to decimal feet
 * Example: 5 feet 10 inches = 5.833 feet
 */
export function feetInchesToDecimalFeet(feet: number, inches: number): number {
  return feet + (inches / 12);
}

/**
 * Convert decimal feet to feet and inches string
 * Example: 5.833 -> "5' 10\""
 */
export function decimalFeetToFeetInches(decimalFeet: number): string {
  const feet = Math.floor(decimalFeet);
  const inches = Math.round((decimalFeet - feet) * 12);
  return `${feet}' ${inches}"`;
}
