import { useCallback, useMemo, useState } from 'react';
import {
  abandon as engineAbandon,
  applyAutoFillNotes as engineApplyAutoFillNotes,
  clearCell as engineClearCell,
  createGame,
  placeValue as enginePlaceValue,
  requestHint as engineRequestHint,
  setNotesMode as engineSetNotesMode,
  toggleNote as engineToggleNote,
  toggleNotesMode as engineToggleNotesMode,
  undo as engineUndo,
  type CellValue,
  type CreateGameInput,
  type GameState,
} from '@sudoke/sudoku-core';

export interface UseGameEngineInput extends CreateGameInput {
  /** Pre-seeded state (used by dev screens / replay). Overrides createGame on mount. */
  readonly seedState?: GameState;
}

export interface UseGameEngine {
  readonly state: GameState;
  readonly selectedIndex: number | null;
  readonly selectedValue: CellValue | null;
  selectCell: (index: number) => void;
  selectValue: (value: CellValue | null) => void;
  place: (value: CellValue) => void;
  toggleNote: (value: CellValue) => void;
  clear: () => void;
  toggleNotesMode: () => void;
  setNotesMode: (on: boolean) => void;
  undo: () => void;
  abandon: () => void;
  reset: () => void;
  /** Casual-only: reveal one correct value, locking the cell. No-op in ranked. */
  requestHint: () => number | null;
  /** Casual-only: pre-populate every empty cell with legal candidates. */
  applyAutoFillNotes: () => void;
}

/**
 * React-friendly wrapper around the pure `sudoku-core` engine. Keeps the
 * selected cell, the active number, and the engine state in sync.
 *
 * The hook only renders when state actually changes (no-op actions return the
 * same reference so React bails out).
 */
export function useGameEngine(initial: UseGameEngineInput): UseGameEngine {
  const [state, setState] = useState<GameState>(() => initial.seedState ?? createGame(initial));
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [selectedValue, setSelectedValue] = useState<CellValue | null>(null);

  const selectCell = useCallback(
    (index: number) => {
      setSelectedIndex(index);
      const cell = state.grid[index];
      if (cell && cell.value !== null && !cell.isWrong) {
        setSelectedValue(cell.value);
      }
    },
    [state.grid],
  );

  const selectValue = useCallback((value: CellValue | null) => {
    setSelectedValue(value);
  }, []);

  const place = useCallback(
    (value: CellValue) => {
      if (selectedIndex === null) return;
      const { state: next } = enginePlaceValue(state, selectedIndex, value);
      if (next === state) return;
      setState(next);
    },
    [selectedIndex, state],
  );

  const toggleNote = useCallback(
    (value: CellValue) => {
      if (selectedIndex === null) return;
      const next = engineToggleNote(state, selectedIndex, value);
      if (next === state) return;
      setState(next);
    },
    [selectedIndex, state],
  );

  const clear = useCallback(() => {
    if (selectedIndex === null) return;
    const next = engineClearCell(state, selectedIndex);
    if (next === state) return;
    setState(next);
  }, [selectedIndex, state]);

  const toggleNotesMode = useCallback(() => {
    setState((prev) => engineToggleNotesMode(prev));
  }, []);

  const setNotesMode = useCallback((on: boolean) => {
    setState((prev) => engineSetNotesMode(prev, on));
  }, []);

  const undo = useCallback(() => {
    setState((prev) => engineUndo(prev));
  }, []);

  const abandon = useCallback(() => {
    setState((prev) => engineAbandon(prev));
  }, []);

  const reset = useCallback(() => {
    setState(initial.seedState ?? createGame(initial));
    setSelectedIndex(null);
    setSelectedValue(null);
  }, [initial]);

  const requestHint = useCallback((): number | null => {
    const { state: next, hintIndex } = engineRequestHint(state, { selectedIndex });
    if (next === state) return null;
    setState(next);
    if (hintIndex !== null) setSelectedIndex(hintIndex);
    return hintIndex;
  }, [state, selectedIndex]);

  const applyAutoFillNotes = useCallback(() => {
    setState((prev) => engineApplyAutoFillNotes(prev));
  }, []);

  return useMemo(
    () => ({
      state,
      selectedIndex,
      selectedValue,
      selectCell,
      selectValue,
      place,
      toggleNote,
      clear,
      toggleNotesMode,
      setNotesMode,
      undo,
      abandon,
      reset,
      requestHint,
      applyAutoFillNotes,
    }),
    [
      state,
      selectedIndex,
      selectedValue,
      selectCell,
      selectValue,
      place,
      toggleNote,
      clear,
      toggleNotesMode,
      setNotesMode,
      undo,
      abandon,
      reset,
      requestHint,
      applyAutoFillNotes,
    ],
  );
}
