import { useEffect, useState } from 'react';
import { Text } from 'react-native';
import { colors, fontSize } from '@/theme/tokens';

interface CountdownProps {
  readonly endsAt: string;
  readonly label?: string;
  readonly style?: object;
}

function formatRemaining(ms: number): string {
  if (ms <= 0) return '00:00:00';
  const totalSec = Math.floor(ms / 1000);
  const hours = Math.floor(totalSec / 3600);
  const minutes = Math.floor((totalSec % 3600) / 60);
  const seconds = totalSec % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

export function Countdown({ endsAt, label = "Today's puzzle ends in", style }: CountdownProps) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const remaining = new Date(endsAt).getTime() - now;
  return (
    <Text
      style={[
        { color: colors.textMuted, fontSize: fontSize.sm },
        style,
      ]}
      accessibilityLabel={`${label} ${formatRemaining(remaining)}`}
    >
      {label} {formatRemaining(remaining)}
    </Text>
  );
}
