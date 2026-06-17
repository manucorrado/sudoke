/**
 * Tier badge for competitive rating (PRD §14.12).
 *
 * Cosmetic only — bands map 1:1 to the server's `tier_for_rating`. Render
 * uses a colored pill with the tier name and the numeric rating beside it.
 */

import { StyleSheet, Text, View } from 'react-native';
import type { RatingTier } from '@/lib/sdk';
import { fontSize, radius, spacing } from '@/theme/tokens';

const TIER_COLORS: Record<RatingTier, { bg: string; fg: string }> = {
  bronze: { bg: '#F4E5D3', fg: '#7A4F1D' },
  silver: { bg: '#E5E7EB', fg: '#4B5563' },
  gold: { bg: '#FFE9A8', fg: '#7A5300' },
  platinum: { bg: '#D1ECEC', fg: '#1F6F6F' },
  diamond: { bg: '#D7E1FF', fg: '#1F3FA1' },
  master: { bg: '#F3D6FF', fg: '#5A1F8A' },
};

const TIER_LABELS: Record<RatingTier, string> = {
  bronze: 'Bronze',
  silver: 'Silver',
  gold: 'Gold',
  platinum: 'Platinum',
  diamond: 'Diamond',
  master: 'Master',
};

interface TierBadgeProps {
  readonly tier: RatingTier;
  readonly rating: number;
  readonly provisional?: boolean;
}

export function TierBadge({ tier, rating, provisional }: TierBadgeProps) {
  const palette = TIER_COLORS[tier];
  return (
    <View
      style={[styles.row, { backgroundColor: palette.bg }]}
      accessibilityRole="text"
      accessibilityLabel={`Rating ${rating}, ${TIER_LABELS[tier]}${provisional ? ', provisional' : ''}`}
    >
      <Text style={[styles.tier, { color: palette.fg }]}>{TIER_LABELS[tier]}</Text>
      <Text style={[styles.rating, { color: palette.fg }]}>{rating}</Text>
      {provisional ? (
        <Text style={[styles.provisional, { color: palette.fg }]}>· Provisional</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'baseline',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    alignSelf: 'flex-start',
    gap: spacing.xs,
  },
  tier: { fontSize: fontSize.xs, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase' },
  rating: { fontSize: fontSize.md, fontWeight: '700' },
  provisional: { fontSize: fontSize.xs, fontWeight: '600' },
});

export function tierLabel(tier: RatingTier): string {
  return TIER_LABELS[tier];
}
