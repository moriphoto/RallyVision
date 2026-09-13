type PlayerId = 'teamA' | 'teamB';

interface GameState {
  scores: Record<PlayerId, number>;
  server: PlayerId;
  isDeuce: boolean;
  winner: PlayerId | null;
}

function updateServer(state: GameState, totalPoints: number): PlayerId {
  if (state.isDeuce || totalPoints >= 20) {
    state.isDeuce = true;
    return state.server === 'teamA' ? 'teamB' : 'teamA';
  }
  return totalPoints % 2 === 0 ? (state.server === 'teamA' ? 'teamB' : 'teamA') : state.server;
}

function checkWin(scores: Record<PlayerId, number>): PlayerId | null {
  if (scores.teamA >= 11 && scores.teamA - scores.teamB >= 2) return 'teamA';
  if (scores.teamB >= 11 && scores.teamB - scores.teamA >= 2) return 'teamB';
  return null;
}

function createGameState(): GameState {
  return {
    scores: { teamA: 0, teamB: 0 },
    server: 'teamA',
    isDeuce: false,
    winner: null
  };
}

function awardPoint(state: GameState, scorer: PlayerId): GameState {
  if (state.winner) {
    return state;
  }
  state.scores[scorer] += 1;
  const totalPoints = state.scores.teamA + state.scores.teamB;
  state.server = updateServer(state, totalPoints);
  state.winner = checkWin(state.scores);
  return state;
}

function resetGame(): GameState {
  return createGameState();
}

export type { PlayerId, GameState };
export { updateServer, checkWin, createGameState, awardPoint, resetGame };
