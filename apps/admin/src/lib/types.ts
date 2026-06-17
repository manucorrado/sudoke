export type PuzzleDifficulty = 'easy' | 'medium' | 'hard' | 'expert';

export type PuzzleStatus =
  | 'imported'
  | 'needs_review'
  | 'approved'
  | 'rejected'
  | 'archived';

export type DailyPuzzleStatus =
  | 'scheduled'
  | 'active'
  | 'finalizing'
  | 'finalized'
  | 'cancelled';

export interface AdminPuzzle {
  readonly id: string;
  readonly givens: string;
  readonly solution: string;
  readonly difficulty: PuzzleDifficulty;
  readonly status: PuzzleStatus;
  readonly estimated_min_seconds: number;
  readonly estimated_max_seconds: number;
  readonly clue_count: number;
  readonly source: string | null;
  readonly license: string | null;
  readonly notes: string | null;
  readonly reviewer_id: string | null;
  readonly reviewed_at: string | null;
  readonly review_notes: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface AdminDailyPuzzle {
  readonly id: string;
  readonly puzzle_id: string;
  readonly scheduled_for: string;
  readonly activate_at: string;
  readonly finalize_at: string;
  readonly status: DailyPuzzleStatus;
  readonly difficulty: PuzzleDifficulty | null;
}

export interface ScheduleEntry {
  readonly puzzle_id: string;
  readonly scheduled_for: string;
}
