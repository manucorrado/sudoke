import { MAX_RANKED_MISTAKES } from './constants';
import type { CasualRules, RankedRules } from './types';

export const RANKED_RULES: RankedRules = Object.freeze({
  mode: 'ranked',
  maxMistakes: MAX_RANKED_MISTAKES,
  autoFillNotes: false,
  hintsEnabled: false,
  autoClearNotes: true,
});

export const DEFAULT_CASUAL_RULES: CasualRules = Object.freeze({
  mode: 'casual',
  maxMistakes: 3,
  hintsEnabled: true,
  autoFillNotes: false,
  autoClearNotes: true,
});

export interface CasualOverrides {
  readonly maxMistakes?: number | null;
  readonly hintsEnabled?: boolean;
  readonly autoFillNotes?: boolean;
  readonly autoClearNotes?: boolean;
  readonly mode?: 'casual' | 'practice';
}

export function makeCasualRules(overrides: CasualOverrides = {}): CasualRules {
  return {
    mode: overrides.mode ?? DEFAULT_CASUAL_RULES.mode,
    maxMistakes:
      overrides.maxMistakes === undefined ? DEFAULT_CASUAL_RULES.maxMistakes : overrides.maxMistakes,
    hintsEnabled: overrides.hintsEnabled ?? DEFAULT_CASUAL_RULES.hintsEnabled,
    autoFillNotes: overrides.autoFillNotes ?? DEFAULT_CASUAL_RULES.autoFillNotes,
    autoClearNotes: overrides.autoClearNotes ?? DEFAULT_CASUAL_RULES.autoClearNotes,
  };
}

export function makeRankedRules(
  overrides: { readonly autoClearNotes?: boolean } = {},
): RankedRules {
  return {
    ...RANKED_RULES,
    autoClearNotes: overrides.autoClearNotes ?? RANKED_RULES.autoClearNotes,
  };
}
