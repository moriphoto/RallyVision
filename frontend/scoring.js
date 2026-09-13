(function (global) {
  function updateServer(state, totalPoints) {
    if (state.isDeuce || totalPoints >= 20) {
      state.isDeuce = true;
      return state.server === 'teamA' ? 'teamB' : 'teamA';
    }
    return totalPoints % 2 === 0
      ? (state.server === 'teamA' ? 'teamB' : 'teamA')
      : state.server;
  }

  function checkWin(scores) {
    if (scores.teamA >= 11 && scores.teamA - scores.teamB >= 2) return 'teamA';
    if (scores.teamB >= 11 && scores.teamB - scores.teamA >= 2) return 'teamB';
    return null;
  }

  function createGameState() {
    return {
      scores: { teamA: 0, teamB: 0 },
      server: 'teamA',
      isDeuce: false,
      winner: null
    };
  }

  function awardPoint(state, scorer) {
    if (state.winner) {
      return state;
    }
    state.scores[scorer] += 1;
    const totalPoints = state.scores.teamA + state.scores.teamB;
    state.server = updateServer(state, totalPoints);
    state.winner = checkWin(state.scores);
    return state;
  }

  function resetGame() {
    return createGameState();
  }

  global.RallyScoring = {
    updateServer,
    checkWin,
    createGameState,
    awardPoint,
    resetGame
  };
})(window);
