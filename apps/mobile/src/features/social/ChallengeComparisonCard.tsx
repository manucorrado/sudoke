import { StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

export type ChallengeOutcome = 'win' | 'lose' | 'tie' | 'pending';

interface ChallengeComparisonCardProps {
  readonly challengerName: string;
  readonly challengerDurationMs: number | null;
  readonly challengerMistakes: number | null;
  readonly recipientDurationMs: number;
  readonly recipientMistakes: number;
  readonly outcome: ChallengeOutcome;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function mistakesLabel(count: number | null): string {
  if (count === null) return 'mistakes pending';
  return `${count} ${count === 1 ? 'mistake' : 'mistakes'}`;
}

function outcomeLabel(outcome: ChallengeOutcome, challengerName: string): string {
  if (outcome === 'win') return 'You win!';
  if (outcome === 'lose') return `${challengerName} wins`;
  if (outcome === 'tie') return 'Tie!';
  return `You finished — waiting for ${challengerName}'s time`;
}

export function ChallengeComparisonCard({
  challengerName,
  challengerDurationMs,
  challengerMistakes,
  recipientDurationMs,
  recipientMistakes,
  outcome,
}: ChallengeComparisonCardProps) {
  return (
    <View
      style={styles.card}
      accessibilityLabel={`Challenge result. ${outcomeLabel(outcome, challengerName)}`}
    >
      <Text style={styles.kicker}>Challenge result</Text>
      <Text style={styles.title}>{outcomeLabel(outcome, challengerName)}</Text>

      <View style={styles.scoreRow}>
        <View style={styles.scoreCell}>
          <Text style={styles.scoreName}>You</Text>
          <Text style={styles.scoreTime}>{formatDuration(recipientDurationMs)}</Text>
          <Text style={styles.scoreMeta}>{mistakesLabel(recipientMistakes)}</Text>
        </View>
        <Text style={styles.vs}>vs</Text>
        <View style={styles.scoreCell}>
          <Text style={styles.scoreName}>{challengerName}</Text>
          <Text style={styles.scoreTime}>
            {challengerDurationMs !== null ? formatDuration(challengerDurationMs) : 'Pending'}
          </Text>
          <Text style={styles.scoreMeta}>{mistakesLabel(challengerMistakes)}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '700',
  },
  title: { fontSize: fontSize.xl, color: colors.text, fontWeight: '800' },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  scoreCell: {
    flex: 1,
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: 2,
  },
  scoreName: { fontSize: fontSize.sm, color: colors.textMuted, fontWeight: '700' },
  scoreTime: { fontSize: fontSize.lg, color: colors.text, fontWeight: '800' },
  scoreMeta: { fontSize: fontSize.xs, color: colors.textMuted },
  vs: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
});
