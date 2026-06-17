import type { PuzzleDifficulty } from './types';

export const GRID_SIZE = 9;
export const BOX_SIZE = 3;
export const TOTAL_CELLS = GRID_SIZE * GRID_SIZE;
export const MAX_RANKED_MISTAKES = 3;
export const PREVIEW_DURATION_SECONDS = 30;

export const DIFFICULTIES: readonly PuzzleDifficulty[] = [
  'easy',
  'medium',
  'hard',
  'expert',
] as const;

/** Ranked rotation - aligned with §10.2 of the PRD. */
export const DEFAULT_WEEKLY_ROTATION: readonly PuzzleDifficulty[] = [
  'easy', // Mon
  'medium', // Tue
  'medium', // Wed
  'hard', // Thu
  'medium', // Fri
  'hard', // Sat
  'hard', // Sun
] as const;

export const DIFFICULTY_MULTIPLIERS: Record<PuzzleDifficulty, number> = {
  easy: 0.85,
  medium: 1.0,
  hard: 1.1,
  expert: 1.25,
};

/**
 * Conservative absolute anti-cheat thresholds (in seconds) per §26.2.
 * Below these times an attempt is flagged for review.
 */
export const SUSPICIOUS_SOLVE_THRESHOLDS_SECONDS: Record<PuzzleDifficulty, number> = {
  easy: 60,
  medium: 90,
  hard: 150,
  expert: 240,
};

/** Default estimated solve-time ranges shown to users (§10.4). */
export const DEFAULT_SOLVE_TIME_ESTIMATES: Record<
  PuzzleDifficulty,
  { min: number; max: number }
> = {
  easy: { min: 180, max: 360 },
  medium: { min: 360, max: 720 },
  hard: { min: 600, max: 1200 },
  expert: { min: 900, max: 1800 },
};
