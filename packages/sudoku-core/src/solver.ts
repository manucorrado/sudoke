import { GRID_SIZE, TOTAL_CELLS } from './constants';
import { boxOf, colOf, rowOf } from './grid';
import type { CellValue, RawGrid, SolutionGrid } from './types';

/**
 * Backtracking Sudoku solver with bitmask peer tracking.
 *
 * - `solve(grid)`: returns one solution or null if unsolvable.
 * - `hasUniqueSolution(grid)`: short-circuits once a second solution is found.
 *
 * Designed for puzzles small enough that this is fast (<10ms for typical
 * MVP-difficulty puzzles). The solver is deterministic so unit tests can
 * rely on stable solutions for a given grid.
 */

interface SolverState {
  cells: (CellValue | 0)[];
  rowMask: number[];
  colMask: number[];
  boxMask: number[];
}

function bit(value: CellValue): number {
  return 1 << (value - 1);
}

function initState(grid: RawGrid): SolverState | null {
  const cells: (CellValue | 0)[] = grid.slice() as (CellValue | 0)[];
  const rowMask = Array<number>(GRID_SIZE).fill(0);
  const colMask = Array<number>(GRID_SIZE).fill(0);
  const boxMask = Array<number>(GRID_SIZE).fill(0);
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const v = cells[i];
    if (!v) continue;
    const r = rowOf(i);
    const c = colOf(i);
    const b = boxOf(i);
    const m = bit(v);
    if ((rowMask[r]! & m) || (colMask[c]! & m) || (boxMask[b]! & m)) {
      return null;
    }
    rowMask[r] = rowMask[r]! | m;
    colMask[c] = colMask[c]! | m;
    boxMask[b] = boxMask[b]! | m;
  }
  return { cells, rowMask, colMask, boxMask };
}

function findBestCell(state: SolverState): { index: number; candidates: number } {
  let bestIndex = -1;
  let bestCandidates = 0;
  let bestCount = 10;
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    if (state.cells[i]) continue;
    const used = state.rowMask[rowOf(i)]! | state.colMask[colOf(i)]! | state.boxMask[boxOf(i)]!;
    const candidates = ~used & 0x1ff;
    const count = popcount(candidates);
    if (count < bestCount) {
      bestCount = count;
      bestCandidates = candidates;
      bestIndex = i;
      if (count <= 1) break;
    }
  }
  return { index: bestIndex, candidates: bestCandidates };
}

function popcount(n: number): number {
  let x = n;
  x = x - ((x >> 1) & 0x55555555);
  x = (x & 0x33333333) + ((x >> 2) & 0x33333333);
  return (((x + (x >> 4)) & 0x0f0f0f0f) * 0x01010101) >> 24;
}

function search(state: SolverState, limit: number, found: SolutionGrid[]): void {
  if (found.length >= limit) return;
  const { index, candidates } = findBestCell(state);
  if (index === -1) {
    found.push(state.cells.slice() as SolutionGrid);
    return;
  }
  if (candidates === 0) return;
  const r = rowOf(index);
  const c = colOf(index);
  const b = boxOf(index);
  let remaining = candidates;
  while (remaining !== 0 && found.length < limit) {
    const m = remaining & -remaining;
    remaining &= remaining - 1;
    const v = (Math.log2(m) + 1) as CellValue;
    state.cells[index] = v;
    state.rowMask[r] = state.rowMask[r]! | m;
    state.colMask[c] = state.colMask[c]! | m;
    state.boxMask[b] = state.boxMask[b]! | m;
    search(state, limit, found);
    state.cells[index] = 0;
    state.rowMask[r] = state.rowMask[r]! & ~m;
    state.colMask[c] = state.colMask[c]! & ~m;
    state.boxMask[b] = state.boxMask[b]! & ~m;
  }
}

export function solve(grid: RawGrid): SolutionGrid | null {
  const state = initState(grid);
  if (!state) return null;
  const found: SolutionGrid[] = [];
  search(state, 1, found);
  return found[0] ?? null;
}

export function findSolutions(grid: RawGrid, limit: number): readonly SolutionGrid[] {
  const state = initState(grid);
  if (!state) return [];
  const found: SolutionGrid[] = [];
  search(state, limit, found);
  return found;
}

export function hasUniqueSolution(grid: RawGrid): boolean {
  return findSolutions(grid, 2).length === 1;
}
