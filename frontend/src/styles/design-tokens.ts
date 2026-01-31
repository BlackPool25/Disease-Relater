/**
 * Design Tokens for Disease Visualizer
 * 
 * Centralized design system constants for the 3D disease network visualization.
 * These tokens define the visual language of the application including colors,
 * typography, spacing, and animation timing.
 * 
 * AESTHETIC: Medical-scientific with a modern, data-visualization feel.
 * Dark mode primary with high-contrast accent colors for risk levels.
 */

// =============================================================================
// COLOR PALETTE
// =============================================================================

/**
 * Primary color palette - Deep scientific blues with warm accents
 */
export const colors = {
  // Brand colors
  primary: {
    50: '#EBF8FF',
    100: '#BEE3F8',
    200: '#90CDF4',
    300: '#63B3ED',
    400: '#4299E1',
    500: '#3182CE',  // Main brand blue
    600: '#2B6CB0',
    700: '#2C5282',
    800: '#2A4365',
    900: '#1A365D',
  },
  
  // Secondary - Purple for data visualization depth
  secondary: {
    50: '#FAF5FF',
    100: '#E9D8FD',
    200: '#D6BCFA',
    300: '#B794F4',
    400: '#9F7AEA',
    500: '#805AD5',  // Main secondary
    600: '#6B46C1',
    700: '#553C9A',
    800: '#44337A',
    900: '#322659',
  },
  
  // Background colors - Dark theme optimized for 3D visualization
  background: {
    dark: '#0A0F1A',      // Deep space background
    darkAlt: '#121929',   // Slightly lighter panels
    card: '#1A2235',      // Card surfaces
    hover: '#243049',     // Interactive hover states
    light: '#F7FAFC',     // Light mode fallback
  },
  
  // Risk level colors - High contrast for quick recognition
  risk: {
    veryHigh: '#E53E3E',  // Red - immediate attention
    high: '#DD6B20',      // Orange - elevated concern
    moderate: '#D69E2E',  // Yellow/Gold - caution
    low: '#38A169',       // Green - healthy range
    none: '#718096',      // Gray - neutral/unknown
  },
  
  // ICD Chapter colors - Distinct hues for 3D network visualization
  chapters: {
    I: '#FF6B6B',    // Infectious diseases
    II: '#845EC2',   // Neoplasms
    III: '#D65DB1',  // Blood disorders
    IV: '#FF9671',   // Metabolic
    V: '#FFC75F',    // Mental
    VI: '#F9F871',   // Nervous
    VII: '#00D4FF',  // Eye
    VIII: '#00C9A7', // Ear
    IX: '#FF6F91',   // Cardiovascular
    X: '#4D8076',    // Respiratory
    XI: '#B39CD0',   // Digestive
    XII: '#FF9F1C',  // Skin
    XIII: '#00B4D8', // Musculoskeletal
    XIV: '#90BE6D',  // Genitourinary
    XV: '#F8A5C2',   // Pregnancy
    XVI: '#95D5B2',  // Perinatal
    XVII: '#BDB2FF', // Congenital
    XVIII: '#E0AAFF',// Symptoms
    XIX: '#FFD6A5',  // Injury
    XX: '#CAFFBF',   // External causes
    XXI: '#A0C4FF',  // Health factors
  },
  
  // Text colors
  text: {
    primary: '#F7FAFC',   // High contrast on dark
    secondary: '#A0AEC0', // Subdued labels
    muted: '#718096',     // Hints and placeholders
    accent: '#63B3ED',    // Links and highlights
    dark: '#1A202C',      // Dark text for light mode
  },
  
  // Utility colors
  border: {
    subtle: 'rgba(255, 255, 255, 0.08)',
    default: 'rgba(255, 255, 255, 0.16)',
    strong: 'rgba(255, 255, 255, 0.24)',
  },
} as const;


// =============================================================================
// TYPOGRAPHY
// =============================================================================

/**
 * Typography system - Modern, clean, data-focused
 * 
 * Uses JetBrains Mono for numbers/data display (monospace)
 * Uses Inter/System fonts for UI text
 */
export const typography = {
  // Font families
  fontFamily: {
    display: "'Space Grotesk', 'SF Pro Display', -apple-system, sans-serif",
    body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    mono: "'JetBrains Mono', 'SF Mono', 'Consolas', monospace",
  },
  
  // Font sizes - Using a modular scale (1.25 ratio)
  fontSize: {
    xs: '0.75rem',     // 12px - Fine print
    sm: '0.875rem',    // 14px - Secondary text
    base: '1rem',      // 16px - Body text
    lg: '1.125rem',    // 18px - Large body
    xl: '1.25rem',     // 20px - Section headers
    '2xl': '1.5rem',   // 24px - Page headers
    '3xl': '1.875rem', // 30px - Hero text
    '4xl': '2.25rem',  // 36px - Display
    '5xl': '3rem',     // 48px - Large display
  },
  
  // Font weights
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  // Line heights
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
  
  // Letter spacing
  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
  },
} as const;


// =============================================================================
// SPACING
// =============================================================================

/**
 * Spacing scale - 4px base unit
 */
export const spacing = {
  px: '1px',
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  1.5: '0.375rem',  // 6px
  2: '0.5rem',      // 8px
  2.5: '0.625rem',  // 10px
  3: '0.75rem',     // 12px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  8: '2rem',        // 32px
  10: '2.5rem',     // 40px
  12: '3rem',       // 48px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
} as const;


// =============================================================================
// BORDERS & SHADOWS
// =============================================================================

export const borderRadius = {
  none: '0',
  sm: '0.25rem',    // 4px
  default: '0.5rem', // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  full: '9999px',
} as const;

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  default: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  glow: {
    primary: '0 0 20px rgba(49, 130, 206, 0.4)',
    risk: '0 0 20px rgba(229, 62, 62, 0.4)',
    success: '0 0 20px rgba(56, 161, 105, 0.4)',
  },
} as const;


// =============================================================================
// ANIMATION & TRANSITIONS
// =============================================================================

export const animation = {
  // Transition durations
  duration: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
    slower: '750ms',
  },
  
  // Easing functions
  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
} as const;


// =============================================================================
// BREAKPOINTS
// =============================================================================

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;


// =============================================================================
// Z-INDEX SCALE
// =============================================================================

export const zIndex = {
  hide: -1,
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const;


// =============================================================================
// 3D VISUALIZATION SPECIFIC
// =============================================================================

/**
 * Constants for the Three.js 3D disease network visualization
 */
export const viz3D = {
  // Camera settings
  camera: {
    fov: 60,
    near: 0.1,
    far: 1000,
    defaultPosition: [0, 0, 5] as const,
  },
  
  // Node (disease) appearance
  node: {
    baseRadius: 0.05,
    minRadius: 0.02,
    maxRadius: 0.2,
    selectedScale: 1.5,
    hoverScale: 1.2,
  },
  
  // Edge (relationship) appearance
  edge: {
    minWidth: 0.5,
    maxWidth: 3,
    opacity: {
      default: 0.3,
      hover: 0.6,
      selected: 0.9,
    },
  },
  
  // Animation
  orbitSpeed: 0.001,
  transitionDuration: 0.5,
} as const;


// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get risk level color based on score (0-1)
 */
export function getRiskColor(score: number): string {
  if (score >= 0.75) return colors.risk.veryHigh;
  if (score >= 0.5) return colors.risk.high;
  if (score >= 0.25) return colors.risk.moderate;
  if (score > 0) return colors.risk.low;
  return colors.risk.none;
}

/**
 * Get ICD chapter color
 */
export function getChapterColor(chapterCode: string): string {
  const key = chapterCode as keyof typeof colors.chapters;
  return colors.chapters[key] || colors.secondary[500];
}

/**
 * Convert hex color to RGB array for Three.js
 */
export function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [1, 1, 1];
  return [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255,
  ];
}
