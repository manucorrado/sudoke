import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface MistakeIndicatorProps {
  readonly current: number;
  readonly max: number | null;
}

export function MistakeIndicator({ current, max }: MistakeIndicatorProps) {
  const isFinalWarning = max !== null && current >= max;
  const label =
    max === null
      ? `Mistakes: ${current}`
      : `Mistakes: ${current}/${max}`;
  return (
    <View style={[styles.container, isFinalWarning && styles.containerWarning]}>
      <Text style={[styles.text, isFinalWarning && styles.textWarning]}>{label}</Text>
      {isFinalWarning ? (
        <Text style={styles.warningText}>Final mistake — one more ends this run.</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
  },
  containerWarning: { backgroundColor: colors.dangerMuted },
  text: { fontSize: fontSize.sm, color: colors.text, fontWeight: '600' },
  textWarning: { color: colors.danger },
  warningText: { fontSize: fontSize.xs, color: colors.danger, marginTop: 2 },
});
