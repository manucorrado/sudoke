import { Pressable, StyleSheet, Text, View } from 'react-native';
import {
  ALL_VALUES,
  isNumberComplete,
  type CellValue,
  type PlayerGrid,
} from '@sudoke/sudoku-core';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface NumberPadProps {
  readonly grid: PlayerGrid;
  readonly notesMode: boolean;
  readonly selectedValue: CellValue | null;
  readonly onPressNumber: (value: CellValue) => void;
  readonly onErase: () => void;
  readonly onToggleNotes: () => void;
  readonly onUndo: () => void;
  readonly canUndo: boolean;
  readonly disabled?: boolean;
  /** Casual-only: show a hint action. Pass `undefined` to hide. */
  readonly onHint?: () => void;
}

/**
 * Number pad + secondary actions (notes, erase, undo).
 *
 * Disables completed numbers per PRD §8.20. When a number is selected,
 * highlights it so the player has visual feedback for number-first input.
 */
export function NumberPad({
  grid,
  notesMode,
  selectedValue,
  onPressNumber,
  onErase,
  onToggleNotes,
  onUndo,
  canUndo,
  disabled = false,
  onHint,
}: NumberPadProps) {
  return (
    <View style={styles.container}>
      <View style={styles.actionsRow}>
        <ActionButton
          label="Undo"
          icon="↶"
          onPress={onUndo}
          disabled={!canUndo || disabled}
          accessibilityLabel="Undo"
        />
        <ActionButton
          label="Erase"
          icon="⌫"
          onPress={onErase}
          disabled={disabled}
          accessibilityLabel="Erase"
        />
        <ActionButton
          label="Notes"
          icon="✎"
          onPress={onToggleNotes}
          active={notesMode}
          disabled={disabled}
          accessibilityLabel={`Toggle notes mode (currently ${notesMode ? 'on' : 'off'})`}
        />
        {onHint ? (
          <ActionButton
            label="Hint"
            icon="💡"
            onPress={onHint}
            disabled={disabled}
            accessibilityLabel="Reveal a correct value (casual only)"
          />
        ) : null}
      </View>
      <View style={styles.numbersRow}>
        {ALL_VALUES.map((value) => {
          const complete = isNumberComplete(grid, value);
          const active = selectedValue === value && !complete;
          return (
            <Pressable
              key={value}
              onPress={() => onPressNumber(value)}
              disabled={complete || disabled}
              accessibilityRole="button"
              accessibilityLabel={`Number ${value}${complete ? ', complete' : ''}`}
              accessibilityState={{ disabled: complete || disabled, selected: active }}
              style={[
                styles.numberButton,
                active && styles.numberButtonActive,
                complete && styles.numberButtonComplete,
              ]}
            >
              <Text
                style={[
                  styles.numberText,
                  active && styles.numberTextActive,
                  complete && styles.numberTextComplete,
                ]}
              >
                {value}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

interface ActionButtonProps {
  readonly label: string;
  readonly icon: string;
  readonly onPress: () => void;
  readonly disabled?: boolean;
  readonly active?: boolean;
  readonly accessibilityLabel: string;
}

function ActionButton({
  label,
  icon,
  onPress,
  disabled = false,
  active = false,
  accessibilityLabel,
}: ActionButtonProps) {
  return (
    <Pressable
      style={[styles.actionButton, active && styles.actionButtonActive]}
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled, selected: active }}
    >
      <Text style={[styles.actionIcon, disabled && styles.actionTextDisabled]}>{icon}</Text>
      <Text
        style={[
          styles.actionLabel,
          active && styles.actionLabelActive,
          disabled && styles.actionTextDisabled,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { width: '100%', paddingHorizontal: spacing.md, gap: spacing.md },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    gap: spacing.sm,
  },
  actionButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonActive: { backgroundColor: colors.primaryMuted },
  actionIcon: { fontSize: 20, color: colors.text },
  actionLabel: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
  actionLabelActive: { color: colors.primary, fontWeight: '600' },
  actionTextDisabled: { color: colors.border },
  numbersRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.xs,
  },
  numberButton: {
    flex: 1,
    aspectRatio: 1,
    minHeight: 36,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberButtonActive: { backgroundColor: colors.primary },
  numberButtonComplete: { backgroundColor: colors.surfaceAlt, opacity: 0.4 },
  numberText: { fontSize: 22, fontWeight: '600', color: colors.text },
  numberTextActive: { color: colors.textInverse },
  numberTextComplete: { color: colors.textMuted },
});
