import { GameScreen } from '@/features/game/GameScreen';
import { DEV_PUZZLE, DEV_SCENARIOS } from '@/features/game/devStates';
import { makeRankedRules } from '@sudoke/sudoku-core';

export default function DevBoardInProgress() {
  return (
    <GameScreen
      title="Ranked · in progress"
      initial={{
        puzzle: DEV_PUZZLE,
        rules: makeRankedRules(),
        seedState: DEV_SCENARIOS.inProgress.build(),
      }}
    />
  );
}
