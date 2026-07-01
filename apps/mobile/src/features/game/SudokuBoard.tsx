import { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import {
  ALL_VALUES,
  boxOf,
  findConflicts,
  GRID_SIZE,
  highlightPeers,
  TOTAL_CELLS,
  type CellState,
  type CellValue,
  type PlayerGrid,
} from '@sudoke/sudoku-core';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface SudokuBoardProps {
  readonly grid: PlayerGrid;
  readonly selectedIndex: number | null;
  readonly selectedValue: CellValue | null;
  readonly onSelectCell: (index: number) => void;
  /** Disable interactions (e.g. after completion). */
  readonly disabled?: boolean;
}

/**
 * 9x9 Sudoku board.
 *
 * - Highlights row/col/box peers of the selected cell.
 * - Highlights cells whose value matches the active number.
 * - Marks duplicate conflicts (any cell sharing the same value in row/col/box).
 * - Shows pencil notes when a cell has no final value.
 *
 * Pure presentational — all state lives in `useGameEngine`.
 */
export function SudokuBoard({
  grid,
  selectedIndex,
  selectedValue,
  onSelectCell,
  disabled = false,
}: SudokuBoardProps) {
  const peerSet = useMemo<ReadonlySet<number>>(
    () => (selectedIndex === null ? new Set() : new Set(highlightPeers(selectedIndex))),
    [selectedIndex],
  );

  const conflictSet = useMemo<ReadonlySet<number>>(() => {
    const set = new Set<number>();
    const flat = grid.map((cell) => cell.value);
    for (let i = 0; i < TOTAL_CELLS; i += 1) {
      const v = grid[i]?.value;
      if (!v) continue;
      const c = findConflicts(flat, i, v);
      if (c.length > 0) {
        set.add(i);
        for (const peer of c) set.add(peer);
      }
    }
    return set;
  }, [grid]);

  return (
    <View style={styles.boardWrap} accessibilityLabel="Sudoku board">
      <View style={styles.board}>
        {Array.from({ length: GRID_SIZE }, (_, row) => (
          <View key={row} style={styles.row}>
            {grid.slice(row * GRID_SIZE, row * GRID_SIZE + GRID_SIZE).map((cell, col) => {
              const index = row * GRID_SIZE + col;
              const box = boxOf(index);
              const isSelected = selectedIndex === index;
              const isPeer = peerSet.has(index);
              const isSameValue =
                selectedValue !== null && cell.value === selectedValue && !cell.isWrong;
              const isConflict = conflictSet.has(index);
              const selectedCell =
                selectedIndex !== null ? (grid[selectedIndex] ?? null) : null;
              const sameBoxAsSelected =
                selectedCell !== null && boxOf(selectedIndex!) === box;
              return (
                <CellView
                  key={index}
                  index={index}
                  cell={cell}
                  row={row}
                  col={col}
                  isSelected={isSelected}
                  isPeer={isPeer}
                  isSameValue={isSameValue}
                  isConflict={isConflict}
                  sameBoxAsSelected={sameBoxAsSelected}
                  onPress={onSelectCell}
                  disabled={disabled}
                />
              );
            })}
          </View>
        ))}
      </View>
    </View>
  );
}

interface CellViewProps {
  readonly index: number;
  readonly cell: CellState;
  readonly row: number;
  readonly col: number;
  readonly isSelected: boolean;
  readonly isPeer: boolean;
  readonly isSameValue: boolean;
  readonly isConflict: boolean;
  readonly sameBoxAsSelected: boolean;
  readonly disabled: boolean;
  readonly onPress: (index: number) => void;
}

function CellView({
  index,
  cell,
  row,
  col,
  isSelected,
  isPeer,
  isSameValue,
  isConflict,
  sameBoxAsSelected,
  disabled,
  onPress,
}: CellViewProps) {
  const cellStyles = [
    styles.cell,
    col % 3 === 0 && styles.cellBoxLeft,
    row % 3 === 0 && styles.cellBoxTop,
    col === GRID_SIZE - 1 && styles.cellEdgeRight,
    row === GRID_SIZE - 1 && styles.cellEdgeBottom,
    isPeer && styles.cellPeer,
    sameBoxAsSelected && !isSelected && styles.cellPeer,
    isSameValue && styles.cellSameValue,
    cell.isWrong && styles.cellWrong,
    isConflict && !cell.isWrong && styles.cellConflict,
    isSelected && styles.cellSelected,
  ];

  const textColor = cell.isWrong
    ? colors.playerWrong
    : cell.isGiven
      ? colors.given
      : colors.playerCorrect;

  const accessibilityLabel = cell.value
    ? `Row ${row + 1} Column ${col + 1}, ${cell.value}${cell.isGiven ? ' given' : ''}${
        cell.isWrong ? ', wrong' : cell.isLocked ? ', locked' : ''
      }`
    : `Row ${row + 1} Column ${col + 1}, empty`;

  // Color-blind-safe cue (PRD §13.4): show an icon in addition to color
  // so wrong/conflict cells are perceivable without relying on hue.
  const cue =
    cell.isWrong ? '✕' : isConflict ? '!' : null;

  return (
    <Pressable
      style={cellStyles}
      onPress={() => onPress(index)}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ selected: isSelected, disabled }}
    >
      {cell.value !== null ? (
        <Text
          style={[
            styles.cellText,
            { color: textColor },
            cell.isGiven && styles.cellTextGiven,
          ]}
        >
          {cell.value}
        </Text>
      ) : cell.notes.length > 0 ? (
        <NotesGrid notes={cell.notes} />
      ) : null}
      {cue ? (
        <Text
          style={[styles.cellCue, cell.isWrong ? styles.cellCueWrong : styles.cellCueConflict]}
          accessibilityElementsHidden
        >
          {cue}
        </Text>
      ) : null}
    </Pressable>
  );
}

function NotesGrid({ notes }: { readonly notes: readonly CellValue[] }) {
  return (
    <View style={styles.notesGrid}>
      {ALL_VALUES.map((v) => (
        <Text key={v} style={styles.note}>
          {notes.includes(v) ? v : ' '}
        </Text>
      ))}
    </View>
  );
}

const CELL_SIZE = 36;
const BOARD_SIZE = CELL_SIZE * GRID_SIZE;

const styles = StyleSheet.create({
  boardWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.sm,
  },
  board: {
    width: BOARD_SIZE,
    height: BOARD_SIZE,
    borderWidth: 2,
    borderColor: colors.borderStrong,
    borderRadius: radius.sm,
    backgroundColor: colors.bg,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    width: '100%',
    height: CELL_SIZE,
  },
  cell: {
    flex: 1,
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    borderRightWidth: StyleSheet.hairlineWidth,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.bg,
  },
  cellBoxLeft: {
    borderLeftWidth: 1.5,
    borderLeftColor: colors.borderStrong,
  },
  cellBoxTop: {
    borderTopWidth: 1.5,
    borderTopColor: colors.borderStrong,
  },
  cellEdgeRight: { borderRightWidth: 0 },
  cellEdgeBottom: { borderBottomWidth: 0 },
  cellPeer: { backgroundColor: colors.highlight },
  cellSameValue: { backgroundColor: colors.highlightStrong },
  cellSelected: { backgroundColor: colors.selection },
  cellConflict: { backgroundColor: colors.warningMuted },
  cellWrong: { backgroundColor: colors.dangerMuted },
  cellText: {
    fontSize: fontSize.cellValue,
    fontWeight: '500',
  },
  cellTextGiven: { fontWeight: '700' },
  notesGrid: {
    width: '100%',
    height: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 2,
    paddingTop: 1,
  },
  note: {
    width: '33.333%',
    textAlign: 'center',
    fontSize: 9,
    color: colors.noteText,
    lineHeight: 10,
  },
  cellCue: {
    position: 'absolute',
    top: 1,
    right: 2,
    fontSize: 9,
    fontWeight: '700',
  },
  cellCueWrong: { color: colors.danger },
  cellCueConflict: { color: colors.warning },
});
