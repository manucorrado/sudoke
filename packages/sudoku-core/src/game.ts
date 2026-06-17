import { TOTAL_CELLS } from './constants';
import {
  boxIndexes,
  boxOf,
  colIndexes,
  colOf,
  rowIndexes,
  rowOf,
} from './grid';
import type {
  CellState,
  CellValue,
  GameAction,
  GameRules,
  GameState,
  PlaceResult,
  PlayerGrid,
  Puzzle,
} from './types';

/**
 * Core gameplay state machine.
 *
 * All transitions are pure functions: `(state, action) -> next state`.
 * Mistake counting, locking, auto-clear-notes, completion and failure are
 * encoded here so the same engine runs on mobile, web, and the server
 * validator.
 *
 * PRD references: §8 (ranked rules), §9 (casual), §13 (gameplay UX).
 */

const EMPTY_CELL: CellState = Object.freeze({
  value: null,
  isGiven: false,
  isLocked: false,
  isWrong: false,
  notes: [],
});

function emptyCell(): CellState {
  return { ...EMPTY_CELL, notes: [] };
}

function givenCell(value: CellValue): CellState {
  return {
    value,
    isGiven: true,
    isLocked: true,
    isWrong: false,
    notes: [],
  };
}

export function createInitialGrid(puzzle: Puzzle): PlayerGrid {
  const grid: CellState[] = [];
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const v = puzzle.givens[i];
    grid.push(v === 0 || v === undefined ? emptyCell() : givenCell(v));
  }
  return grid;
}

export interface CreateGameInput {
  readonly puzzle: Puzzle;
  readonly rules: GameRules;
  readonly notesMode?: boolean;
}

export function createGame({ puzzle, rules, notesMode = false }: CreateGameInput): GameState {
  return {
    puzzle,
    grid: createInitialGrid(puzzle),
    rules,
    mistakes: 0,
    status: 'in_progress',
    notesMode,
    history: [],
    future: [],
  };
}

function setCell(grid: PlayerGrid, index: number, next: CellState): PlayerGrid {
  const out = grid.slice();
  out[index] = next;
  return out;
}

function peersForAutoClear(index: number): readonly number[] {
  const seen = new Set<number>();
  rowIndexes(rowOf(index)).forEach((i) => seen.add(i));
  colIndexes(colOf(index)).forEach((i) => seen.add(i));
  boxIndexes(boxOf(index)).forEach((i) => seen.add(i));
  seen.delete(index);
  return Array.from(seen);
}

function boardIsComplete(grid: PlayerGrid, solution: readonly CellValue[]): boolean {
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const cell = grid[i];
    if (!cell || cell.value === null || cell.isWrong) return false;
    if (cell.value !== solution[i]) return false;
  }
  return true;
}

function isFailure(state: GameState, nextMistakes: number): boolean {
  const max = state.rules.maxMistakes;
  if (max === null) return false;
  return nextMistakes > max;
}

export function toggleNotesMode(state: GameState): GameState {
  return { ...state, notesMode: !state.notesMode };
}

export function setNotesMode(state: GameState, on: boolean): GameState {
  return { ...state, notesMode: on };
}

/**
 * Place a final value into a cell. Enforces PRD §8 rules:
 * - cannot place into given or locked cells,
 * - re-tapping the same wrong value is a no-op (§8.3),
 * - correct values lock the cell (§8.8),
 * - wrong values increment mistake counter (§8.1),
 * - auto-clear notes from peers on correct placement (§8.18),
 * - auto-submit triggers when the board is full and conflict-free (§8.14).
 */
export function placeValue(state: GameState, index: number, value: CellValue): PlaceResult {
  if (state.status !== 'in_progress') {
    return { state, action: noopAction(index), mistakeAdded: false, completed: false };
  }
  const cell = state.grid[index];
  if (!cell) throw new Error(`Invalid cell index ${index}`);
  if (cell.isGiven || cell.isLocked) {
    return { state, action: noopAction(index), mistakeAdded: false, completed: false };
  }
  // No-op when re-tapping the same wrong value (§8.3).
  if (cell.value === value) {
    return { state, action: noopAction(index), mistakeAdded: false, completed: false };
  }

  const solutionValue = state.puzzle.solution[index];
  const isCorrect = solutionValue === value;
  const previousValue = cell.value;
  const previousNotes = cell.notes;

  let nextGrid: PlayerGrid = setCell(state.grid, index, {
    value,
    isGiven: false,
    isLocked: isCorrect,
    isWrong: !isCorrect,
    notes: [],
  });

  const autoCleared: { index: number; value: CellValue }[] = [];
  if (isCorrect && state.rules.autoClearNotes) {
    for (const peerIdx of peersForAutoClear(index)) {
      const peer = nextGrid[peerIdx];
      if (!peer || peer.value !== null) continue;
      if (peer.notes.includes(value)) {
        nextGrid = setCell(nextGrid, peerIdx, {
          ...peer,
          notes: peer.notes.filter((n) => n !== value),
        });
        autoCleared.push({ index: peerIdx, value });
      }
    }
  }

  const mistakeAdded = !isCorrect;
  const nextMistakes = state.mistakes + (mistakeAdded ? 1 : 0);
  const completed = boardIsComplete(nextGrid, state.puzzle.solution);
  const failed = isFailure(state, nextMistakes);

  const action: GameAction = {
    type: 'place_value',
    index,
    value,
    previous: previousValue,
    previousNotes,
    wasCorrect: isCorrect,
    autoCleared,
  };

  const nextStatus: GameState['status'] = failed
    ? 'failed'
    : completed
      ? 'completed'
      : 'in_progress';

  const nextState: GameState = {
    ...state,
    grid: nextGrid,
    mistakes: nextMistakes,
    status: nextStatus,
    history: [...state.history, action],
    future: [],
  };

  return { state: nextState, action, mistakeAdded, completed: nextStatus === 'completed' };
}

/** Toggle a single note candidate. No-op on cells with a final value (§8.16). */
export function toggleNote(state: GameState, index: number, value: CellValue): GameState {
  if (state.status !== 'in_progress') return state;
  const cell = state.grid[index];
  if (!cell || cell.value !== null) return state;
  const has = cell.notes.includes(value);
  const nextNotes = has ? cell.notes.filter((n) => n !== value) : [...cell.notes, value].sort();
  const action: GameAction = { type: 'toggle_note', index, value, added: !has };
  return {
    ...state,
    grid: setCell(state.grid, index, { ...cell, notes: nextNotes }),
    history: [...state.history, action],
    future: [],
  };
}

/** Clear a cell. Locked/given cells cannot be cleared. */
export function clearCell(state: GameState, index: number): GameState {
  if (state.status !== 'in_progress') return state;
  const cell = state.grid[index];
  if (!cell || cell.isGiven || cell.isLocked) return state;
  if (cell.value === null && cell.notes.length === 0) return state;
  const action: GameAction = {
    type: 'clear_cell',
    index,
    previousValue: cell.value,
    previousNotes: cell.notes,
  };
  return {
    ...state,
    grid: setCell(state.grid, index, emptyCell()),
    history: [...state.history, action],
    future: [],
  };
}

/** Replace notes for a cell wholesale. Used by paint-notes / undo. */
export function setNotes(
  state: GameState,
  index: number,
  notes: readonly CellValue[],
): GameState {
  if (state.status !== 'in_progress') return state;
  const cell = state.grid[index];
  if (!cell || cell.value !== null) return state;
  const sorted = [...new Set(notes)].sort() as CellValue[];
  const action: GameAction = {
    type: 'set_notes',
    index,
    previous: cell.notes,
    next: sorted,
  };
  return {
    ...state,
    grid: setCell(state.grid, index, { ...cell, notes: sorted }),
    history: [...state.history, action],
    future: [],
  };
}

/**
 * Abandon the attempt (manual or external trigger).
 * In ranked context this means the attempt is consumed without rating.
 */
export function abandon(state: GameState): GameState {
  if (state.status !== 'in_progress') return state;
  return { ...state, status: 'abandoned' };
}

/**
 * Undo the last reversible action. Locked correct entries cannot be undone
 * even if they appear last in history (§8.9).
 */
export function undo(state: GameState): GameState {
  if (state.status !== 'in_progress' || state.history.length === 0) return state;
  const last = state.history[state.history.length - 1]!;
  if (last.type === 'place_value' && last.wasCorrect) return state;

  const newHistory = state.history.slice(0, -1);
  let nextGrid: PlayerGrid = state.grid;

  switch (last.type) {
    case 'place_value': {
      const cell = state.grid[last.index];
      if (!cell) return state;
      nextGrid = setCell(state.grid, last.index, {
        value: last.previous,
        isGiven: false,
        isLocked: false,
        isWrong: last.previous !== null && state.puzzle.solution[last.index] !== last.previous,
        notes: last.previousNotes,
      });
      if (last.autoCleared) {
        for (const restored of last.autoCleared) {
          const peer = nextGrid[restored.index];
          if (!peer) continue;
          if (peer.value !== null) continue;
          if (peer.notes.includes(restored.value)) continue;
          nextGrid = setCell(nextGrid, restored.index, {
            ...peer,
            notes: [...peer.notes, restored.value].sort() as CellValue[],
          });
        }
      }
      break;
    }
    case 'toggle_note': {
      const cell = state.grid[last.index];
      if (!cell || cell.value !== null) return state;
      const restored = last.added
        ? cell.notes.filter((n) => n !== last.value)
        : ([...cell.notes, last.value].sort() as CellValue[]);
      nextGrid = setCell(state.grid, last.index, { ...cell, notes: restored });
      break;
    }
    case 'clear_cell': {
      const cell = state.grid[last.index];
      if (!cell) return state;
      const restoredCell: CellState = {
        value: last.previousValue,
        isGiven: cell.isGiven,
        isLocked: false,
        isWrong:
          last.previousValue !== null &&
          state.puzzle.solution[last.index] !== last.previousValue,
        notes: last.previousNotes,
      };
      nextGrid = setCell(state.grid, last.index, restoredCell);
      break;
    }
    case 'set_notes': {
      const cell = state.grid[last.index];
      if (!cell || cell.value !== null) return state;
      nextGrid = setCell(state.grid, last.index, { ...cell, notes: last.previous });
      break;
    }
    default:
      assertNever(last);
  }

  return {
    ...state,
    grid: nextGrid,
    history: newHistory,
    future: [last, ...state.future],
  };
}

/** Returns the count of placed instances of `value`, used for number-pad complete state. */
export function countPlaced(grid: PlayerGrid, value: CellValue): number {
  let n = 0;
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const cell = grid[i];
    if (cell && cell.value === value && !cell.isWrong) n += 1;
  }
  return n;
}

/** True if all 9 instances of `value` are correctly placed (§8.20). */
export function isNumberComplete(grid: PlayerGrid, value: CellValue): boolean {
  return countPlaced(grid, value) === 9;
}

/** Returns peer cells that share a row/col/box with `index`. */
export function highlightPeers(index: number): readonly number[] {
  return peersForAutoClear(index);
}

function noopAction(index: number): GameAction {
  return { type: 'toggle_note', index, value: 1, added: false };
}

function assertNever(value: never): never {
  throw new Error(`Unhandled action: ${String(value)}`);
}

/** Convenience selectors. */
export const selectors = {
  isComplete(state: GameState): boolean {
    return state.status === 'completed';
  },
  isFailed(state: GameState): boolean {
    return state.status === 'failed';
  },
  mistakesRemaining(state: GameState): number | null {
    if (state.rules.maxMistakes === null) return null;
    return Math.max(0, state.rules.maxMistakes - state.mistakes);
  },
  isFinalMistake(state: GameState): boolean {
    if (state.rules.maxMistakes === null) return false;
    return state.mistakes === state.rules.maxMistakes;
  },
};
