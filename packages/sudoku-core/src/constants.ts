import type { PuzzleDifficulty } from './types';

export const GRID_SIZE = 9;
export const BOX_SIZE = 3;
export const MAX_RANKED_MISTAKES = 3;

export const DIFFICULTIES: readonly PuzzleDifficulty[] = ['easy', 'medium', 'hard'] as const;

export const DIFFICULTY_MULTIPLIERS: Record<PuzzleDifficulty, number> = {
  easy: 0.85,
  medium: 1.0,
  hard: 1.1,
};

export const PREVIEW_DURATION_SECONDS = 30;
