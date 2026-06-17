import {
  createGame,
  FIXTURE_PUZZLES,
  makeCasualRules,
  makeRankedRules,
  placeValue,
  toggleNote,
  TOTAL_CELLS,
  type CellValue,
  type GameState,
  type Puzzle,
} from '@sudoke/sudoku-core';

const PUZZLE: Puzzle = FIXTURE_PUZZLES[0]!;

interface ScenarioBuilder {
  readonly title: string;
  readonly build: () => GameState;
}

function emptyIndexes(state: GameState): number[] {
  const out: number[] = [];
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const cell = state.grid[i];
    if (cell && !cell.isGiven && cell.value === null) out.push(i);
  }
  return out;
}

function applyCorrects(state: GameState, count: number): GameState {
  let next = state;
  let placed = 0;
  for (let i = 0; i < TOTAL_CELLS && placed < count; i += 1) {
    const cell = next.grid[i];
    if (!cell || cell.isGiven || cell.value !== null) continue;
    const v = PUZZLE.solution[i]!;
    next = placeValue(next, i, v).state;
    placed += 1;
  }
  return next;
}

function applyMistakes(state: GameState, count: number): GameState {
  let next = state;
  const targets = emptyIndexes(next);
  for (let i = 0; i < count && i < targets.length; i += 1) {
    const idx = targets[i]!;
    const correct = PUZZLE.solution[idx]!;
    const wrong: CellValue = (correct === 1 ? 2 : 1) as CellValue;
    next = placeValue(next, idx, wrong).state;
  }
  return next;
}

function fillSolution(state: GameState): GameState {
  let next = state;
  for (let i = 0; i < TOTAL_CELLS; i += 1) {
    const cell = next.grid[i];
    if (!cell || cell.isGiven) continue;
    const v = PUZZLE.solution[i]!;
    const res = placeValue(next, i, v);
    next = res.state;
    if (res.completed) break;
  }
  return next;
}

function sprinkleNotes(state: GameState, candidates: readonly CellValue[]): GameState {
  let next = state;
  let count = 0;
  for (let i = 0; i < TOTAL_CELLS && count < 6; i += 1) {
    const cell = next.grid[i];
    if (!cell || cell.isGiven || cell.value !== null) continue;
    for (const c of candidates) {
      next = toggleNote(next, i, c);
    }
    count += 1;
  }
  return next;
}

export const DEV_SCENARIOS = {
  inProgress: {
    title: 'Ranked · in progress',
    build: () => {
      let state = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
      state = applyCorrects(state, 5);
      state = sprinkleNotes(state, [2, 4, 7]);
      return state;
    },
  },
  mistakes: {
    title: 'Ranked · 2 mistakes',
    build: () => {
      let state = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
      state = applyCorrects(state, 4);
      state = applyMistakes(state, 2);
      return state;
    },
  },
  failed: {
    title: 'Ranked · failed',
    build: () => {
      let state = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
      state = applyMistakes(state, 4);
      return state;
    },
  },
  completed: {
    title: 'Ranked · completed',
    build: () => {
      const state = createGame({ puzzle: PUZZLE, rules: makeRankedRules() });
      return fillSolution(state);
    },
  },
  casual: {
    title: 'Casual · unlimited',
    build: () => {
      let state = createGame({
        puzzle: PUZZLE,
        rules: makeCasualRules({ maxMistakes: null, autoClearNotes: true }),
      });
      state = applyCorrects(state, 3);
      state = applyMistakes(state, 1);
      return state;
    },
  },
} as const satisfies Record<string, ScenarioBuilder>;

export { PUZZLE as DEV_PUZZLE };
