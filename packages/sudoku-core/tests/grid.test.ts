import { describe, expect, it } from 'vitest';
import {
  boxOf,
  colOf,
  findConflicts,
  isCompleteSolution,
  isPlacementValid,
  parseGridString,
  peersOf,
  rowOf,
  serializeGrid,
} from '../src';

describe('grid utilities', () => {
  it('computes row/col/box for known indices', () => {
    expect(rowOf(0)).toBe(0);
    expect(colOf(0)).toBe(0);
    expect(boxOf(0)).toBe(0);

    expect(rowOf(40)).toBe(4);
    expect(colOf(40)).toBe(4);
    expect(boxOf(40)).toBe(4);

    expect(rowOf(80)).toBe(8);
    expect(colOf(80)).toBe(8);
    expect(boxOf(80)).toBe(8);
  });

  it('peersOf returns 20 unique cells', () => {
    expect(peersOf(0)).toHaveLength(20);
    expect(new Set(peersOf(0)).size).toBe(20);
  });

  it('parses and round-trips a grid string', () => {
    const raw = '530070000600195000098000060800060003400803001700020006060000280000419005000080079';
    const parsed = parseGridString(raw);
    expect(parsed).toHaveLength(81);
    expect(serializeGrid(parsed)).toBe(raw);
  });

  it('rejects malformed grid strings', () => {
    expect(() => parseGridString('123')).toThrow();
    expect(() => parseGridString('a'.repeat(81))).toThrow();
  });

  it('isPlacementValid catches row/col/box conflicts', () => {
    const grid = parseGridString('5' + '0'.repeat(80));
    expect(isPlacementValid(grid, 1, 5)).toBe(false);
    expect(isPlacementValid(grid, 1, 3)).toBe(true);
  });

  it('findConflicts returns conflicting peer indexes', () => {
    const grid = parseGridString('5' + '0'.repeat(8) + '5' + '0'.repeat(71));
    expect(findConflicts(grid, 1, 5)).toEqual(expect.arrayContaining([0, 9]));
  });

  it('isCompleteSolution detects valid and invalid grids', () => {
    const valid = parseGridString(
      '534678912' +
        '672195348' +
        '198342567' +
        '859761423' +
        '426853791' +
        '713924856' +
        '961537284' +
        '287419635' +
        '345286179',
    );
    expect(isCompleteSolution(valid)).toBe(true);

    const broken = parseGridString('1' + '0'.repeat(80));
    expect(isCompleteSolution(broken)).toBe(false);
  });
});
