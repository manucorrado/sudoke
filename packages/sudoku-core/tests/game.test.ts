import { describe, expect, it } from 'vitest';
import {
  abandon,
  clearCell,
  createGame,
  FIXTURE_PUZZLES,
  isNumberComplete,
  makeCasualRules,
  makeRankedRules,
  placeValue,
  selectors,
  setNotes,
  toggleNote,
  undo,
} from '../src';
import type { CellValue, GameState } from '../src';

const PUZZLE = FIXTURE_PUZZLES[0]!;

function newRankedGame(): GameState {
  return createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
}

function firstEmptyIndex(state: GameState): number {
  for (let i = 0; i < state.grid.length; i += 1) {
    const cell = state.grid[i];
    if (cell && cell.value === null && !cell.isGiven) return i;
  }
  throw new Error('no empty cell');
}

describe('game — ranked rules', () => {
  it('locks correct entries and prevents further edits', () => {
    const game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    const { state, mistakeAdded } = placeValue(game, idx, correct);
    expect(mistakeAdded).toBe(false);
    expect(state.grid[idx]!.isLocked).toBe(true);
    expect(state.grid[idx]!.value).toBe(correct);

    const other = correct === 1 ? (2 as CellValue) : (1 as CellValue);
    const second = placeValue(state, idx, other);
    expect(second.state.grid[idx]!.value).toBe(correct);
  });

  it('counts wrong entries as mistakes and fails on the 4th', () => {
    let game = newRankedGame();
    const targets: number[] = [];
    for (let i = 0; i < game.grid.length && targets.length < 4; i += 1) {
      const cell = game.grid[i];
      if (cell && !cell.isGiven && cell.value === null) targets.push(i);
    }
    expect(targets.length).toBe(4);

    for (let i = 0; i < 3; i += 1) {
      const idx = targets[i]!;
      const correct = PUZZLE.solution[idx]!;
      const wrong = (correct === 1 ? 2 : 1) as CellValue;
      const { state, mistakeAdded } = placeValue(game, idx, wrong);
      expect(mistakeAdded).toBe(true);
      game = state;
    }
    expect(game.mistakes).toBe(3);
    expect(selectors.isFinalMistake(game)).toBe(true);
    expect(game.status).toBe('in_progress');

    const idx = targets[3]!;
    const correct = PUZZLE.solution[idx]!;
    const wrong = (correct === 1 ? 2 : 1) as CellValue;
    const { state } = placeValue(game, idx, wrong);
    expect(state.mistakes).toBe(4);
    expect(state.status).toBe('failed');
  });

  it('does not count a re-tap of the same wrong value as a new mistake', () => {
    const game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    const wrong = (correct === 1 ? 2 : 1) as CellValue;
    const first = placeValue(game, idx, wrong);
    expect(first.mistakeAdded).toBe(true);
    const second = placeValue(first.state, idx, wrong);
    expect(second.mistakeAdded).toBe(false);
    expect(second.state.mistakes).toBe(1);
  });

  it('counts repeated wrong-after-correction as separate mistakes (§8.3)', () => {
    let game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    const wrong = (correct === 1 ? 2 : 1) as CellValue;
    game = placeValue(game, idx, wrong).state;
    game = clearCell(game, idx);
    const second = placeValue(game, idx, wrong);
    expect(second.mistakeAdded).toBe(true);
    expect(second.state.mistakes).toBe(2);
  });

  it('auto-clears notes from peers on a correct entry (§8.18)', () => {
    let game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    // Add the same candidate as a note in every peer that's editable.
    for (const peerIdx of peers(idx)) {
      const peer = game.grid[peerIdx];
      if (!peer || peer.isGiven || peer.value !== null) continue;
      game = toggleNote(game, peerIdx, correct);
    }
    const { state } = placeValue(game, idx, correct);
    for (const peerIdx of peers(idx)) {
      const peer = state.grid[peerIdx];
      if (!peer || peer.isGiven || peer.value !== null) continue;
      expect(peer.notes.includes(correct)).toBe(false);
    }
  });

  it('auto-submits when the board is complete (§8.14)', () => {
    let game = newRankedGame();
    for (let i = 0; i < 81; i += 1) {
      const cell = game.grid[i];
      if (!cell || cell.isGiven) continue;
      const v = PUZZLE.solution[i]!;
      const res = placeValue(game, i, v);
      game = res.state;
      if (res.completed) break;
    }
    expect(game.status).toBe('completed');
    expect(selectors.isComplete(game)).toBe(true);
  });

  it('isNumberComplete becomes true once all 9 are placed (§8.20)', () => {
    let game = newRankedGame();
    const target: CellValue = 1;
    for (let i = 0; i < 81; i += 1) {
      const cell = game.grid[i];
      if (!cell) continue;
      if (PUZZLE.solution[i] === target && !cell.isGiven) {
        game = placeValue(game, i, target).state;
      }
    }
    expect(isNumberComplete(game.grid, target)).toBe(true);
  });

  it('undo cannot remove correct locked entries (§8.9)', () => {
    const game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    const placed = placeValue(game, idx, correct).state;
    const after = undo(placed);
    expect(after).toBe(placed);
    expect(after.grid[idx]!.value).toBe(correct);
  });

  it('undo reverts wrong entries and decrements via re-correction', () => {
    const game = newRankedGame();
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    const wrong = (correct === 1 ? 2 : 1) as CellValue;
    const placed = placeValue(game, idx, wrong).state;
    expect(placed.mistakes).toBe(1);
    const undone = undo(placed);
    expect(undone.grid[idx]!.value).toBeNull();
    expect(undone.history.length).toBe(0);
    // Mistakes stay counted (PRD: undo doesn't decrement the wrong-entry counter).
    expect(undone.mistakes).toBe(1);
  });
});

describe('game — casual rules', () => {
  it('unlimited mistakes never fails', () => {
    let game = createGame({
      puzzle: PUZZLE,
      rules: makeCasualRules({ maxMistakes: null }),
    });
    for (let i = 0; i < 5; i += 1) {
      const idx = firstEmptyIndex(game);
      const correct = PUZZLE.solution[idx]!;
      const wrong = (correct === 1 ? 2 : 1) as CellValue;
      game = placeValue(game, idx, wrong).state;
      game = clearCell(game, idx);
    }
    expect(game.status).toBe('in_progress');
    expect(game.mistakes).toBe(5);
  });

  it('rejects notes on cells with a final value (§8.16)', () => {
    let game = createGame({ puzzle: PUZZLE, rules: makeCasualRules() });
    const idx = firstEmptyIndex(game);
    const correct = PUZZLE.solution[idx]!;
    game = placeValue(game, idx, correct).state;
    const after = toggleNote(game, idx, 7);
    expect(after).toBe(game);
  });

  it('setNotes overwrites notes for a cell', () => {
    let game = createGame({ puzzle: PUZZLE, rules: makeCasualRules() });
    const idx = firstEmptyIndex(game);
    game = setNotes(game, idx, [1, 3, 5]);
    expect(game.grid[idx]!.notes).toEqual([1, 3, 5]);
  });
});

describe('game — abandon', () => {
  it('abandon marks status and prevents further mutation', () => {
    let game = newRankedGame();
    game = abandon(game);
    expect(game.status).toBe('abandoned');
    const idx = firstEmptyIndex({ ...game, status: 'in_progress' });
    const after = placeValue(game, idx, 1).state;
    expect(after).toBe(game);
  });
});

function peers(index: number): readonly number[] {
  const set = new Set<number>();
  const row = Math.floor(index / 9);
  const col = index % 9;
  const br = Math.floor(row / 3) * 3;
  const bc = Math.floor(col / 3) * 3;
  for (let c = 0; c < 9; c += 1) set.add(row * 9 + c);
  for (let r = 0; r < 9; r += 1) set.add(r * 9 + col);
  for (let r = br; r < br + 3; r += 1) {
    for (let c = bc; c < bc + 3; c += 1) set.add(r * 9 + c);
  }
  set.delete(index);
  return Array.from(set);
}
