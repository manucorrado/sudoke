import { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import {
  selectors,
  type CellValue,
  type GameState,
} from '@sudoke/sudoku-core';
import type { UseGameEngineInput } from './useGameEngine';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';
import { GameTimer } from './GameTimer';
import { MistakeIndicator } from './MistakeIndicator';
import { NumberPad } from './NumberPad';
import { SudokuBoard } from './SudokuBoard';
import { useGameEngine } from './useGameEngine';

interface GameScreenProps {
  readonly initial: UseGameEngineInput;
  readonly title?: string;
  /** Called when the game reaches a terminal state (completed/failed/abandoned). */
  readonly onTerminal?: (state: GameState) => void;
}

/**
 * Self-contained playable Sudoku screen.
 *
 * Uses the shared sudoku-core engine — no game-state logic lives here.
 * Renders the board, mistake counter, timer, number pad and a small status
 * banner. Both ranked and casual modes share this UI.
 */
export function GameScreen({ initial, title, onTerminal }: GameScreenProps) {
  const game = useGameEngine(initial);
  const [startedAt] = useState(() => Date.now());
  const [stoppedAt, setStoppedAt] = useState<number | null>(null);

  const terminal =
    game.state.status === 'completed' ||
    game.state.status === 'failed' ||
    game.state.status === 'abandoned';

  useEffect(() => {
    if (terminal && stoppedAt === null) {
      const stamp = Date.now();
      setStoppedAt(stamp);
      onTerminal?.(game.state);
    }
  }, [terminal, stoppedAt, onTerminal, game.state]);

  const handleNumber = (value: CellValue) => {
    if (game.selectedIndex === null) {
      game.selectValue(value);
      return;
    }
    if (game.state.notesMode) {
      game.toggleNote(value);
    } else {
      game.place(value);
    }
    game.selectValue(value);
  };

  const canUndo = useMemo(() => {
    if (game.state.history.length === 0) return false;
    const last = game.state.history[game.state.history.length - 1]!;
    if (last.type === 'place_value' && last.wasCorrect) return false;
    return true;
  }, [game.state.history]);

  return (
    <View style={styles.container}>
      {title ? <Text style={styles.title}>{title}</Text> : null}

      <View style={styles.statusBar}>
        <MistakeIndicator current={game.state.mistakes} max={game.state.rules.maxMistakes} />
        <GameTimer startedAt={startedAt} stoppedAt={stoppedAt} />
      </View>

      <SudokuBoard
        grid={game.state.grid}
        selectedIndex={game.selectedIndex}
        selectedValue={game.selectedValue}
        onSelectCell={game.selectCell}
        disabled={terminal}
      />

      <NumberPad
        grid={game.state.grid}
        notesMode={game.state.notesMode}
        selectedValue={game.selectedValue}
        onPressNumber={handleNumber}
        onErase={game.clear}
        onToggleNotes={game.toggleNotesMode}
        onUndo={game.undo}
        canUndo={canUndo && !terminal}
        disabled={terminal}
        {...(game.state.rules.mode !== 'ranked' && game.state.rules.hintsEnabled
          ? { onHint: () => game.requestHint() }
          : {})}
      />

      {terminal ? (
        <View style={styles.terminalCard}>
          {game.state.status === 'completed' ? (
            <>
              <Text style={[styles.terminalTitle, { color: colors.success }]}>Completed!</Text>
              <Text style={styles.terminalSubtitle}>
                Mistakes: {game.state.mistakes}
                {game.state.rules.maxMistakes !== null
                  ? `/${game.state.rules.maxMistakes}`
                  : ''}
              </Text>
            </>
          ) : game.state.status === 'failed' ? (
            <>
              <Text style={[styles.terminalTitle, { color: colors.danger }]}>
                Attempt failed
              </Text>
              <Text style={styles.terminalSubtitle}>
                You used all {game.state.rules.maxMistakes} mistakes.
              </Text>
            </>
          ) : (
            <Text style={[styles.terminalTitle, { color: colors.textMuted }]}>Abandoned</Text>
          )}
          <Pressable onPress={game.reset} style={styles.resetButton}>
            <Text style={styles.resetButtonText}>Try Again (Practice)</Text>
          </Pressable>
        </View>
      ) : null}

      <Text style={styles.helper}>
        {selectors.mistakesRemaining(game.state) === null
          ? 'Unlimited mistakes'
          : `${selectors.mistakesRemaining(game.state)} mistakes remaining`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    gap: spacing.md,
    backgroundColor: colors.bg,
  },
  title: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text, textAlign: 'center' },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
  },
  helper: {
    textAlign: 'center',
    color: colors.textMuted,
    fontSize: fontSize.xs,
    paddingBottom: spacing.md,
  },
  terminalCard: {
    marginHorizontal: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    alignItems: 'center',
    gap: spacing.sm,
  },
  terminalTitle: { fontSize: fontSize.lg, fontWeight: '700' },
  terminalSubtitle: { color: colors.textMuted, fontSize: fontSize.sm },
  resetButton: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    backgroundColor: colors.primary,
  },
  resetButtonText: { color: colors.textInverse, fontWeight: '600' },
});
