type PlayerId = 'teamA' | 'teamB';

interface GameState {
  scores: Record<PlayerId, number>;
  server: PlayerId;
  isDeuce: boolean;
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

export type { PlayerId, GameState };
export { updateServer, checkWin };
