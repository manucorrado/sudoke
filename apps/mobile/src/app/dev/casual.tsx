import { GameScreen } from '@/features/game/GameScreen';
import { DEV_PUZZLE, DEV_SCENARIOS } from '@/features/game/devStates';
import { makeCasualRules } from '@sudoke/sudoku-core';

export default function DevCasual() {
  return (
    <GameScreen
      title="Casual · unlimited"
      initial={{
        puzzle: DEV_PUZZLE,
        rules: makeCasualRules({ maxMistakes: null }),
        seedState: DEV_SCENARIOS.casual.build(),
      }}
    />
  );
}
