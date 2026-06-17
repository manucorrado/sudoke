import { BOX_SIZE, GRID_SIZE, TOTAL_CELLS } from './constants';
import type { CellValue, RawGrid, SolutionGrid } from './types';
import { ALL_VALUES } from './types';

export function indexOf(row: number, col: number): number {
  return row * GRID_SIZE + col;
}

export function rowOf(index: number): number {
  return Math.floor(index / GRID_SIZE);
}

export function colOf(index: number): number {
  return index % GRID_SIZE;
}

export function boxOf(index: number): number {
  return Math.floor(rowOf(index) / BOX_SIZE) * BOX_SIZE + Math.floor(colOf(index) / BOX_SIZE);
}

/** Indexes of every cell in the same row. */
export function rowIndexes(row: number): readonly number[] {
  const out: number[] = [];
  for (let c = 0; c < GRID_SIZE; c += 1) out.push(indexOf(row, c));
  return out;
}

export function colIndexes(col: number): readonly number[] {
  const out: number[] = [];
  for (let r = 0; r < GRID_SIZE; r += 1) out.push(indexOf(r, col));
  return out;
}

export function boxIndexes(box: number): readonly number[] {
  const boxRow = Math.floor(box / BOX_SIZE) * BOX_SIZE;
  const boxCol = (box % BOX_SIZE) * BOX_SIZE;
  const out: number[] = [];
  for (let r = boxRow; r < boxRow + BOX_SIZE; r += 1) {
    for (let c = boxCol; c < boxCol + BOX_SIZE; c += 1) {
      out.push(indexOf(r, c));
    }
  }
  return out;
}

/** Peer cells for a given index (row + col + box, excluding self). */
export function peersOf(index: number): readonly number[] {
  const peers = new Set<number>();
  rowIndexes(rowOf(index)).forEach((i) => peers.add(i));
  colIndexes(colOf(index)).forEach((i) => peers.add(i));
  boxIndexes(boxOf(index)).forEach((i) => peers.add(i));
  peers.delete(index);
  return Array.from(peers);
}

export function isCellValue(n: number): n is CellValue {
  return Number.isInteger(n) && n >= 1 && n <= 9;
}

/**
 * Returns the conflicting peer indexes for a given placement.
 *
 * Useful for highlighting duplicates in the UI without revealing
 * whether the placement is correct vs the solution.
 */
export function findConflicts(
  grid: ReadonlyArray<CellValue | 0 | null>,
  index: number,
  value: CellValue,
): readonly number[] {
  const conflicts: number[] = [];
  for (const peer of peersOf(index)) {
    if (grid[peer] === value) conflicts.push(peer);
  }
  return conflicts;
}

/** Returns true if the placement would create no row/col/box conflicts. */
export function isPlacementValid(
  grid: ReadonlyArray<CellValue | 0 | null>,
  index: number,
  value: CellValue,
): boolean {
  return findConflicts(grid, index, value).length === 0;
}

/** Returns true if `grid` is a valid completed Sudoku solution. */
export function isCompleteSolution(grid: ReadonlyArray<CellValue | 0 | null>): boolean {
  if (grid.length !== TOTAL_CELLS) return false;
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const v = grid[i];
    if (!v || !isCellValue(v)) return false;
  }
  for (let group = 0; group < GRID_SIZE; group += 1) {
    if (!isUniqueGroup(grid, rowIndexes(group))) return false;
    if (!isUniqueGroup(grid, colIndexes(group))) return false;
    if (!isUniqueGroup(grid, boxIndexes(group))) return false;
  }
  return true;
}

function isUniqueGroup(
  grid: ReadonlyArray<CellValue | 0 | null>,
  indexes: readonly number[],
): boolean {
  const seen = new Set<number>();
  for (const i of indexes) {
    const v = grid[i];
    if (typeof v === 'number' && v >= 1 && v <= 9) {
      if (seen.has(v)) return false;
      seen.add(v);
    }
  }
  return true;
}

/** Parse an 81-character string ("0" or "." = empty) into a RawGrid. */
export function parseGridString(input: string): RawGrid {
  const cleaned = input.replace(/\s+/g, '');
  if (cleaned.length !== TOTAL_CELLS) {
    throw new Error(
      `Invalid grid string: expected ${TOTAL_CELLS} cells, got ${cleaned.length}`,
    );
  }
  const grid: (CellValue | 0)[] = [];
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const ch = cleaned[i];
    if (ch === '.' || ch === '0') {
      grid.push(0);
      continue;
    }
    const n = Number(ch);
    if (!isCellValue(n)) {
      throw new Error(`Invalid cell character "${ch}" at index ${i}`);
    }
    grid.push(n);
  }
  return grid;
}

/** Serialize a grid back to an 81-character string ("0" = empty). */
export function serializeGrid(grid: ReadonlyArray<CellValue | 0 | null>): string {
  let out = '';
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const v = grid[i];
    out += v && isCellValue(v) ? String(v) : '0';
  }
  return out;
}

/** Number of given (non-empty) cells in a puzzle. */
export function clueCount(grid: RawGrid): number {
  let n = 0;
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    if (grid[i] !== 0) n += 1;
  }
  return n;
}

/** Returns true if the placement matches the known solution. */
export function isCorrectAgainstSolution(
  solution: SolutionGrid,
  index: number,
  value: CellValue,
): boolean {
  return solution[index] === value;
}

/** All valid values 1..9. Re-exported for convenience. */
export { ALL_VALUES };
