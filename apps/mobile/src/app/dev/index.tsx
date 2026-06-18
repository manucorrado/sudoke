import { Link } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface DevScreen {
  readonly path:
    | '/dev/board-in-progress'
    | '/dev/board-mistakes'
    | '/dev/board-failed'
    | '/dev/board-completed'
    | '/dev/casual'
    | '/dev/board-casual-hinted';
  readonly title: string;
  readonly description: string;
}

const DEV_SCREENS: readonly DevScreen[] = [
  {
    path: '/dev/board-in-progress',
    title: 'Board · In Progress',
    description: 'Fresh ranked board with a few correct placements.',
  },
  {
    path: '/dev/board-mistakes',
    title: 'Board · 2 mistakes',
    description: 'Ranked board with two wrong entries (final-mistake warning at 3).',
  },
  {
    path: '/dev/board-failed',
    title: 'Board · Failed attempt',
    description: 'Four wrong entries — attempt is in failed state.',
  },
  {
    path: '/dev/board-completed',
    title: 'Board · Completed',
    description: 'Fully solved puzzle in completed state.',
  },
  {
    path: '/dev/casual',
    title: 'Board · Casual unlimited',
    description: 'Casual rules with unlimited mistakes.',
  },
  {
    path: '/dev/board-casual-hinted',
    title: 'Board · Casual + hints + auto-fill notes',
    description:
      'Casual mode with hints enabled and notes pre-populated via Auto-Fill Notes (PRD §9).',
  },
];

/**
 * Agent-visible index of dev screens. Each route is a deterministic
 * snapshot of a gameplay state so screenshots and Playwright can hit them
 * directly without needing to set up flows.
 */
export function DevScreensIndex() {
  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
      <Text style={styles.title}>Dev Screens</Text>
      <Text style={styles.subtitle}>
        Agent-visible routes for development, testing, and screenshotting.
      </Text>

      {DEV_SCREENS.map((screen) => (
        <Link key={screen.path} href={screen.path} asChild>
          <View style={styles.card} accessibilityRole="link">
            <Text style={styles.cardTitle}>{screen.title}</Text>
            <Text style={styles.cardDescription}>{screen.description}</Text>
            <Text style={styles.cardPath}>{screen.path}</Text>
          </View>
        </Link>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { flex: 1, backgroundColor: colors.bg },
  container: { padding: spacing.lg, paddingTop: spacing.xxl, gap: spacing.md },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.sm, color: colors.textMuted, marginBottom: spacing.md },
  card: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    gap: 4,
  },
  cardTitle: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  cardDescription: { fontSize: fontSize.sm, color: colors.textMuted },
  cardPath: { fontSize: fontSize.xs, color: colors.primary, fontFamily: 'monospace' },
});

export default DevScreensIndex;
