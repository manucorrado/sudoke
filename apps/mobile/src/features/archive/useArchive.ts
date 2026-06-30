import { useQuery } from '@tanstack/react-query';
import {
  parseGridString,
  solve,
  type Puzzle,
  type PuzzleDifficulty,
} from '@sudoke/sudoku-core';
import {
  sdk,
  type ArchiveDetailDTO,
  type ArchiveListDTO,
  type ArchiveMyResultDTO,
  type UpcomingListDTO,
} from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export function useArchiveList(opts: { limit?: number } = {}) {
  const { authCtx } = useAuth();
  return useQuery<ArchiveListDTO>({
    queryKey: ['archive', 'list', opts.limit ?? null],
    queryFn: () => sdk.getArchive(authCtx, opts),
    staleTime: 60_000,
  });
}

export function useUpcoming(opts: { limit?: number } = {}) {
  const { authCtx } = useAuth();
  return useQuery<UpcomingListDTO>({
    queryKey: ['archive', 'upcoming', opts.limit ?? null],
    queryFn: () => sdk.getUpcoming(authCtx, opts),
    staleTime: 60_000,
  });
}

export function useArchiveDetail(dailyPuzzleId: string | null) {
  const { authCtx } = useAuth();
  return useQuery<ArchiveDetailDTO>({
    queryKey: ['archive', 'detail', dailyPuzzleId],
    enabled: dailyPuzzleId !== null,
    queryFn: () => sdk.getArchiveDetail(dailyPuzzleId!, authCtx),
    staleTime: 5 * 60_000,
  });
}

/**
 * The signed-in player's original ranked result for a closed daily.
 * Disabled for guests (only registered accounts have ranked history).
 */
export function useArchiveMyResult(dailyPuzzleId: string | null) {
  const { authCtx, status } = useAuth();
  return useQuery<ArchiveMyResultDTO>({
    queryKey: ['archive', 'my-result', dailyPuzzleId],
    enabled: dailyPuzzleId !== null && status === 'authenticated',
    queryFn: () => sdk.getArchiveMyResult(dailyPuzzleId!, authCtx),
    retry: false,
    staleTime: 5 * 60_000,
  });
}

/**
 * Convert an archive detail payload into a sudoku-core `Puzzle`.
 * Estimates default to (60s, 600s) when missing.
 */
export function puzzleFromArchive(detail: ArchiveDetailDTO): Puzzle {
  const difficulty = (detail.difficulty as PuzzleDifficulty) ?? 'medium';
  const givens = parseGridString(detail.givens);
  const solution = solve(givens);
  if (!solution) {
    throw new Error(`Archive puzzle ${detail.puzzle_id} could not be solved`);
  }
  return {
    id: detail.puzzle_id,
    givens,
    solution,
    metadata: {
      difficulty,
      estimatedSolveTimeSeconds: {
        min: detail.estimated_min_seconds,
        max: detail.estimated_max_seconds,
      },
      source: 'Archive',
      license: 'CC0',
    },
  };
}
