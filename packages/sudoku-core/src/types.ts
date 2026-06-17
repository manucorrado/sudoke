export type CellValue = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
export type CellIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export type PuzzleDifficulty = 'easy' | 'medium' | 'hard';

export interface Cell {
  value: CellValue | null;
  isGiven: boolean;
  notes: Set<CellValue>;
  isLocked: boolean;
  isWrong: boolean;
}

export type Grid = Cell[][];

export interface PuzzleMetadata {
  difficulty: PuzzleDifficulty;
  estimatedSolveTimeSeconds: { min: number; max: number };
  source?: string;
  license?: string;
}

export interface Puzzle {
  id: string;
  grid: Grid;
  solution: CellValue[][];
  metadata: PuzzleMetadata;
}

export interface GameState {
  puzzle: Puzzle;
  playerGrid: Grid;
  mistakes: number;
  maxMistakes: number;
  isCompleted: boolean;
  isFailed: boolean;
  startedAt: number;
  completedAt: number | null;
}

export interface RankedRules {
  maxMistakes: 3;
  lockCorrectEntries: true;
  immediateWrongDetection: true;
  autoSubmitOnComplete: true;
  allowUndo: true;
  undoCannotUnlockCorrect: true;
}

export interface CasualSettings {
  maxMistakes: number | null;
  hintsEnabled: boolean;
  autoFillNotes: boolean;
  autoClearNotes: boolean;
}
