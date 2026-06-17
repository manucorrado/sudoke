import { describe, expect, it } from 'vitest';
import { hasUniqueSolution, parseGridString, serializeGrid, solve } from '../src';

const EASY =
  '530070000' +
  '600195000' +
  '098000060' +
  '800060003' +
  '400803001' +
  '700020006' +
  '060000280' +
  '000419005' +
  '000080079';

const EASY_SOLUTION =
  '534678912' +
  '672195348' +
  '198342567' +
  '859761423' +
  '426853791' +
  '713924856' +
  '961537284' +
  '287419635' +
  '345286179';

describe('solver', () => {
  it('solves a canonical easy puzzle', () => {
    const grid = parseGridString(EASY);
    const sol = solve(grid);
    expect(sol).not.toBeNull();
    expect(serializeGrid(sol!)).toBe(EASY_SOLUTION);
  });

  it('reports unique solution', () => {
    expect(hasUniqueSolution(parseGridString(EASY))).toBe(true);
  });

  it('detects unsolvable puzzles', () => {
    const conflicting = parseGridString('5' + '5' + '0'.repeat(79));
    expect(solve(conflicting)).toBeNull();
  });

  it('detects non-unique solutions', () => {
    const empty = parseGridString('0'.repeat(81));
    expect(hasUniqueSolution(empty)).toBe(false);
  });
});
