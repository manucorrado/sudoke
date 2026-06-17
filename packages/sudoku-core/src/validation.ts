import { TOTAL_CELLS } from './constants';
import { clueCount, isCellValue, isCompleteSolution, serializeGrid } from './grid';
import { hasUniqueSolution, solve } from './solver';
import type { RawGrid, SolutionGrid } from './types';

export interface PuzzleValidationOk {
  readonly ok: true;
  readonly solution: SolutionGrid;
  readonly clueCount: number;
}

export interface PuzzleValidationError {
  readonly ok: false;
  readonly issues: readonly string[];
}

export type PuzzleValidationResult = PuzzleValidationOk | PuzzleValidationError;

export interface ValidatePuzzleInput {
  readonly givens: RawGrid;
  /** If provided, the solution must match the unique solution. */
  readonly solution?: SolutionGrid;
  /** Minimum clue count (default 17 — fewer cannot have a unique solution). */
  readonly minClues?: number;
}

/**
 * Validates that a puzzle is well-formed:
 * - exactly 81 cells, all 0..9
 * - no row/col/box conflicts among givens
 * - has at least one solution
 * - has exactly one solution
 * - given solution (if any) matches the unique solution
 *
 * This is the gate the admin importer uses before approving puzzles.
 */
export function validatePuzzle(input: ValidatePuzzleInput): PuzzleValidationResult {
  const issues: string[] = [];
  const { givens, solution, minClues = 17 } = input;

  if (givens.length !== TOTAL_CELLS) {
    issues.push(`Givens must have ${TOTAL_CELLS} cells (received ${givens.length})`);
    return { ok: false, issues };
  }

  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const v = givens[i];
    if (v === 0) continue;
    if (typeof v !== 'number' || !isCellValue(v)) {
      issues.push(`Invalid value at index ${i}: ${String(v)}`);
    }
  }
  if (issues.length > 0) return { ok: false, issues };

  const clues = clueCount(givens);
  if (clues < minClues) {
    issues.push(`Puzzle has ${clues} clues; minimum is ${minClues}`);
  }

  const solutions = solve(givens);
  if (solutions === null) {
    issues.push('Puzzle has no solution (givens conflict or unsolvable)');
    return { ok: false, issues: issues.length > 0 ? issues : ['unsolvable'] };
  }

  const unique = hasUniqueSolution(givens);
  if (!unique) {
    issues.push('Puzzle does not have a unique solution');
  }

  if (solution) {
    if (solution.length !== TOTAL_CELLS) {
      issues.push(`Solution must have ${TOTAL_CELLS} cells`);
    } else if (!isCompleteSolution(solution)) {
      issues.push('Provided solution is not a valid completed Sudoku grid');
    } else if (serializeGrid(solution) !== serializeGrid(solutions)) {
      issues.push('Provided solution does not match the computed unique solution');
    } else {
      // Givens must agree with the provided solution at every clue cell.
      for (let i = 0; i < TOTAL_CELLS; i += 1) {
        const g = givens[i];
        if (g !== 0 && g !== solution[i]) {
          issues.push(`Given at index ${i} disagrees with solution`);
          break;
        }
      }
    }
  }

  if (issues.length > 0) return { ok: false, issues };
  return { ok: true, solution: solutions, clueCount: clues };
}
