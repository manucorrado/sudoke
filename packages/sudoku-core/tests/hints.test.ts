import { describe, expect, it } from 'vitest';
import {
  applyAutoFillNotes,
  computeCandidates,
  createGame,
  FIXTURE_PUZZLES,
  makeCasualRules,
  makeRankedRules,
  placeValue,
  requestHint,
  setNotes,
  toggleNote,
  undo,
  type CellValue,
  type GameState,
} from '../src';

const PUZZLE = FIXTURE_PUZZLES[0]!;

function newCasual(overrides: Parameters<typeof makeCasualRules>[0] = {}): GameState {
  return createGame({ puzzle: PUZZLE, rules: makeCasualRules({ hintsEnabled: true, ...overrides }) });
}

function firstEmptyIndex(state: GameState): number {
  for (let i = 0; i < state.grid.length; i += 1) {
    const cell = state.grid[i];
    if (cell && cell.value === null && !cell.isGiven) return i;
  }
  throw new Error('no empty cell');
}

describe('computeCandidates', () => {
  it('returns null for cells with a final value', () => {
    const game = newCasual();
    const givenIndex = game.grid.findIndex((c) => c.isGiven);
    expect(computeCandidates(game.grid, givenIndex)).toBeNull();
  });

  it('excludes values already placed in row/col/box', () => {
    const game = newCasual();
    const idx = firstEmptyIndex(game);
    const candidates = computeCandidates(game.grid, idx);
    expect(candidates).not.toBeNull();
    // Solution value is always a candidate before any placements.
    expect(candidates).toContain(PUZZLE.solution[idx]!);
  });
});

describe('applyAutoFillNotes', () => {
  it('populates notes for every empty cell with candidate sets (§9)', () => {
    const game = newCasual({ autoFillNotes: true });
    const next = applyAutoFillNotes(game);
    expect(next).not.toBe(game);
    for (let i = 0; i < 81; i += 1) {
      const cell = next.grid[i]!;
      if (cell.value !== null) {
        expect(cell.notes).toEqual([]);
      } else {
        expect(cell.notes.length).toBeGreaterThan(0);
        expect(cell.notes).toContain(PUZZLE.solution[i]!);
      }
    }
  });

  it('overwrites prior notes', () => {
    let game = newCasual({ autoFillNotes: true });
    const idx = firstEmptyIndex(game);
    game = setNotes(game, idx, [1, 2]);
    const next = applyAutoFillNotes(game);
    expect(next.grid[idx]!.notes).not.toEqual([1, 2]);
  });

  it('is a no-op in ranked mode', () => {
    const game = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
    const next = applyAutoFillNotes(game);
    expect(next).toBe(game);
  });

  it('is reversible via undo', () => {
    let game = newCasual({ autoFillNotes: true });
    const idx = firstEmptyIndex(game);
    game = toggleNote(game, idx, 1);
    const original = game.grid[idx]!.notes;
    const filled = applyAutoFillNotes(game);
    expect(filled.grid[idx]!.notes).not.toEqual(original);
    const undone = undo(filled);
    expect(undone.grid[idx]!.notes).toEqual(original);
  });
});

describe('requestHint', () => {
  it('reveals the selected empty cell and locks it', () => {
    const game = newCasual();
    const idx = firstEmptyIndex(game);
    const { state, hintIndex, value } = requestHint(game, { selectedIndex: idx });
    expect(hintIndex).toBe(idx);
    expect(value).toBe(PUZZLE.solution[idx]!);
    expect(state.grid[idx]!.value).toBe(PUZZLE.solution[idx]!);
    expect(state.grid[idx]!.isLocked).toBe(true);
    expect(state.mistakes).toBe(0);
  });

  it('falls back to the first empty cell when selection is unusable', () => {
    const game = newCasual();
    const { state, hintIndex } = requestHint(game, { selectedIndex: null });
    expect(hintIndex).not.toBeNull();
    if (hintIndex === null) return;
    expect(state.grid[hintIndex]!.value).toBe(PUZZLE.solution[hintIndex]!);
  });

  it('is a no-op in ranked mode (§9 hints are casual-only)', () => {
    const game = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
    const result = requestHint(game);
    expect(result.state).toBe(game);
    expect(result.hintIndex).toBeNull();
  });

  it('is a no-op when hints are disabled', () => {
    const game = newCasual({ hintsEnabled: false });
    const result = requestHint(game);
    expect(result.state).toBe(game);
    expect(result.hintIndex).toBeNull();
  });

  it('cannot be undone (the truth is out)', () => {
    const game = newCasual();
    const idx = firstEmptyIndex(game);
    const { state } = requestHint(game, { selectedIndex: idx });
    const after = undo(state);
    expect(after).toBe(state);
  });

  it('auto-clears the revealed value from peer notes', () => {
    let game = newCasual();
    const idx = firstEmptyIndex(game);
    const solution = PUZZLE.solution[idx]!;
    const peer = (idx + 1) % 81;
    const peerCell = game.grid[peer]!;
    if (peerCell.value === null && !peerCell.isGiven) {
      game = toggleNote(game, peer, solution);
    }
    const { state } = requestHint(game, { selectedIndex: idx });
    const after = state.grid[peer]!;
    if (after.value === null) {
      expect(after.notes).not.toContain(solution);
    }
  });

  it('completes the board when the hint fills the last empty cell', () => {
    let game = newCasual();
    for (let i = 0; i < 81; i += 1) {
      const cell = game.grid[i]!;
      if (cell.isGiven) continue;
      const target = PUZZLE.solution[i]!;
      if (i === 80 || allButOneFilled(game.grid)) break;
      game = placeValue(game, i, target).state;
    }
    let lastEmpty = -1;
    for (let i = 0; i < 81; i += 1) {
      if (game.grid[i]!.value === null) {
        lastEmpty = i;
        break;
      }
    }
    if (lastEmpty < 0) return;
    const { state } = requestHint(game, { selectedIndex: lastEmpty });
    expect(state.status).toBe('completed');
  });
});

function allButOneFilled(grid: GameState['grid']): boolean {
  let empty = 0;
  for (const cell of grid) if (cell.value === null) empty += 1;
  return empty === 1;
}
