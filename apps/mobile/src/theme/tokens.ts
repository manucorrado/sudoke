/**
 * Design tokens for Sudoke. Single light theme for MVP — extend with dark
 * later. All component styles should reference these tokens rather than
 * inline hex values.
 */

export const colors = {
  bg: '#FFFFFF',
  surface: '#F8F8FB',
  surfaceAlt: '#EFEFF5',
  text: '#1A1A2E',
  textMuted: '#6C6C80',
  textInverse: '#FFFFFF',
  border: '#D8D8E2',
  borderStrong: '#1A1A2E',
  primary: '#3651FF',
  primaryMuted: '#E6EAFF',
  success: '#1FA171',
  successMuted: '#E1F5EC',
  warning: '#E0A800',
  warningMuted: '#FFF6D6',
  danger: '#D62E2E',
  dangerMuted: '#FCE3E3',
  selection: '#DDE6FF',
  highlight: '#EEF2FF',
  highlightStrong: '#C2D0FF',
  given: '#1A1A2E',
  playerCorrect: '#3651FF',
  playerWrong: '#D62E2E',
  noteText: '#6C6C80',
} as const;

export const radius = { sm: 4, md: 8, lg: 12, pill: 999 } as const;
export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;
export const fontSize = {
  xs: 11,
  sm: 13,
  md: 15,
  lg: 17,
  xl: 22,
  xxl: 28,
  cellValue: 24,
} as const;

export const elevation = {
  card: {
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
} as const;

export type Tokens = {
  colors: typeof colors;
  radius: typeof radius;
  spacing: typeof spacing;
  fontSize: typeof fontSize;
};
