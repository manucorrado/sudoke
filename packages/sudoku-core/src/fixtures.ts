import { parseGridString } from './grid';
import { solve } from './solver';
import type { Puzzle, PuzzleDifficulty, RawGrid, SolutionGrid } from './types';
import { DEFAULT_SOLVE_TIME_ESTIMATES } from './constants';

interface FixtureSpec {
  readonly id: string;
  readonly givens: string;
  readonly difficulty: PuzzleDifficulty;
}

const FIXTURE_SPECS: readonly FixtureSpec[] = [
  {
    id: 'fixture-easy-01',
    difficulty: 'easy',
    givens:
      '530070000' +
      '600195000' +
      '098000060' +
      '800060003' +
      '400803001' +
      '700020006' +
      '060000280' +
      '000419005' +
      '000080079',
  },
  {
    id: 'fixture-medium-01',
    difficulty: 'medium',
    givens:
      '004300209' +
      '005009001' +
      '070060043' +
      '006002087' +
      '190007400' +
      '050083000' +
      '600000105' +
      '003508690' +
      '042000300',
  },
  {
    id: 'fixture-hard-01',
    difficulty: 'hard',
    givens:
      '800000000' +
      '003600000' +
      '070090200' +
      '050007000' +
      '000045700' +
      '000100030' +
      '001000068' +
      '008500010' +
      '090000400',
  },
];

function build(spec: FixtureSpec): Puzzle {
  const givens: RawGrid = parseGridString(spec.givens);
  const solution = solve(givens);
  if (!solution) {
    throw new Error(`Fixture ${spec.id} has no solution`);
  }
  return {
    id: spec.id,
    givens,
    solution,
    metadata: {
      difficulty: spec.difficulty,
      estimatedSolveTimeSeconds: DEFAULT_SOLVE_TIME_ESTIMATES[spec.difficulty],
      source: 'Sudoke fixtures',
      license: 'CC0',
    },
  };
}

export const FIXTURE_PUZZLES: readonly Puzzle[] = FIXTURE_SPECS.map(build);

export function getFixture(id: string): Puzzle | undefined {
  return FIXTURE_PUZZLES.find((p) => p.id === id);
}

export function fixtureByDifficulty(difficulty: PuzzleDifficulty): Puzzle | undefined {
  return FIXTURE_PUZZLES.find((p) => p.metadata.difficulty === difficulty);
}

/** Returns the solution for one of the fixtures. */
export function fixtureSolution(id: string): SolutionGrid | undefined {
  return FIXTURE_PUZZLES.find((p) => p.id === id)?.solution;
}
