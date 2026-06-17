import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface GameTimerProps {
  /** Unix ms when timing began. Use server-issued `started_at` in ranked mode. */
  readonly startedAt: number;
  /** When set, the timer freezes at this value. Set on completion/failure. */
  readonly stoppedAt?: number | null;
  /** If true, the value is concealed but still ticking (PRD §13.2). */
  readonly hideToggleable?: boolean;
}

/**
 * Display-only timer. In ranked mode the server owns the official duration —
 * this component is purely for UX feedback.
 */
export function GameTimer({ startedAt, stoppedAt = null, hideToggleable = true }: GameTimerProps) {
  const [now, setNow] = useState(() => Date.now());
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    if (stoppedAt !== null) return undefined;
    const id = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(id);
  }, [stoppedAt]);

  const ms = (stoppedAt ?? now) - startedAt;
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const mm = Math.floor(totalSec / 60)
    .toString()
    .padStart(2, '0');
  const ss = (totalSec % 60).toString().padStart(2, '0');

  return (
    <View style={styles.row}>
      <Text style={styles.label}>Time</Text>
      <Pressable
        onPress={() => hideToggleable && setHidden((v) => !v)}
        accessibilityRole="button"
        accessibilityLabel={`Timer ${hidden ? 'hidden' : `${mm}:${ss}`}, tap to ${hidden ? 'show' : 'hide'}`}
      >
        <Text style={styles.value}>{hidden ? '••:••' : `${mm}:${ss}`}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: spacing.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
  },
  label: { fontSize: fontSize.xs, color: colors.textMuted, fontWeight: '600' },
  value: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text, fontVariant: ['tabular-nums'] },
});
