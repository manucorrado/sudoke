import { GameScreen } from '@/features/game/GameScreen';
import { DEV_SCENARIOS } from '@/features/game/devStates';

const scenario = DEV_SCENARIOS.casualHinted.build();

export default function BoardCasualHintedDev() {
  return (
    <GameScreen
      title={DEV_SCENARIOS.casualHinted.title}
      initial={{ puzzle: scenario.puzzle, rules: scenario.rules, seedState: scenario }}
    />
  );
}
