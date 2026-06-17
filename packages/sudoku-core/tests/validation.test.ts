import { describe, expect, it } from 'vitest';
import { parseGridString, solve, validatePuzzle } from '../src';

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

describe('validatePuzzle', () => {
  it('approves a valid unique-solution puzzle', () => {
    const result = validatePuzzle({ givens: parseGridString(EASY) });
    expect(result.ok).toBe(true);
  });

  it('rejects empty grids (non-unique)', () => {
    const result = validatePuzzle({ givens: parseGridString('0'.repeat(81)) });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.issues.join(' ')).toMatch(/unique|clues/i);
    }
  });

  it('rejects conflicting givens', () => {
    const result = validatePuzzle({
      givens: parseGridString('55' + '0'.repeat(79)),
    });
    expect(result.ok).toBe(false);
  });

  it('cross-checks a provided solution', () => {
    const givens = parseGridString(EASY);
    const solution = solve(givens)!;
    const ok = validatePuzzle({ givens, solution });
    expect(ok.ok).toBe(true);

    const tampered = [...solution];
    tampered[0] = tampered[0] === 1 ? 2 : 1;
    const result = validatePuzzle({ givens, solution: tampered });
    expect(result.ok).toBe(false);
  });
});
