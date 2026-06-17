/**
 * Core types for the Sudoke gameplay engine.
 *
 * The engine is deliberately framework-agnostic: it operates on plain
 * serializable data so the same logic can run on mobile, web, and the API.
 */

export type CellValue = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type CellIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export const ALL_VALUES: readonly CellValue[] = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const;

export type PuzzleDifficulty = 'easy' | 'medium' | 'hard' | 'expert';

/**
 * Raw 9x9 puzzle representation. 0 means empty.
 * Stored as a 81-length array for fast cloning and serialization.
 */
export type RawGrid = readonly (CellValue | 0)[];

/** Solved grid - every cell is filled. */
export type SolutionGrid = readonly CellValue[];

export interface PuzzleMetadata {
  readonly difficulty: PuzzleDifficulty;
  readonly estimatedSolveTimeSeconds: { readonly min: number; readonly max: number };
  readonly source?: string;
  readonly license?: string;
}

export interface Puzzle {
  readonly id: string;
  readonly givens: RawGrid;
  readonly solution: SolutionGrid;
  readonly metadata: PuzzleMetadata;
}

/** Player cell state. */
export interface CellState {
  /** null = empty, otherwise the current final value. */
  readonly value: CellValue | null;
  /** true if this cell came from puzzle givens. */
  readonly isGiven: boolean;
  /**
   * true if a correct final value has been locked in (either given or
   * confirmed correct entry). Locked cells cannot be edited.
   */
  readonly isLocked: boolean;
  /** true if a value is present and it is the wrong final answer. */
  readonly isWrong: boolean;
  /** Pencil candidates. Only meaningful when value === null. */
  readonly notes: readonly CellValue[];
}

export type PlayerGrid = readonly CellState[];

export type AttemptMode = 'ranked' | 'casual' | 'practice';

export type AttemptStatus =
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'abandoned';

export interface RankedRules {
  readonly mode: 'ranked';
  readonly maxMistakes: 3;
  readonly autoFillNotes: false;
  readonly hintsEnabled: false;
  readonly autoClearNotes: boolean;
}

export interface CasualRules {
  readonly mode: 'casual' | 'practice';
  /** null = unlimited. */
  readonly maxMistakes: number | null;
  readonly hintsEnabled: boolean;
  readonly autoFillNotes: boolean;
  readonly autoClearNotes: boolean;
}

export type GameRules = RankedRules | CasualRules;

export interface GameState {
  readonly puzzle: Puzzle;
  readonly grid: PlayerGrid;
  readonly rules: GameRules;
  readonly mistakes: number;
  readonly status: AttemptStatus;
  readonly notesMode: boolean;
  readonly history: readonly GameAction[];
  readonly future: readonly GameAction[];
}

/**
 * Actions that mutate game state. They're recorded for undo and for the
 * server event audit trail.
 */
export type GameAction =
  | { readonly type: 'place_value'; readonly index: number; readonly value: CellValue; readonly previous: CellValue | null; readonly previousNotes: readonly CellValue[]; readonly wasCorrect: boolean; readonly autoCleared?: ReadonlyArray<{ readonly index: number; readonly value: CellValue }> }
  | { readonly type: 'toggle_note'; readonly index: number; readonly value: CellValue; readonly added: boolean }
  | { readonly type: 'clear_cell'; readonly index: number; readonly previousValue: CellValue | null; readonly previousNotes: readonly CellValue[] }
  | { readonly type: 'set_notes'; readonly index: number; readonly previous: readonly CellValue[]; readonly next: readonly CellValue[] }
  | { readonly type: 'auto_fill_notes'; readonly cells: ReadonlyArray<{ readonly index: number; readonly previous: readonly CellValue[]; readonly next: readonly CellValue[] }> }
  | { readonly type: 'hint'; readonly index: number; readonly value: CellValue; readonly previousNotes: readonly CellValue[] };

export interface PlaceResult {
  readonly state: GameState;
  readonly action: GameAction;
  /** True if this place caused a mistake count increment. */
  readonly mistakeAdded: boolean;
  /** True if the board became complete and ready for auto-submit. */
  readonly completed: boolean;
}
