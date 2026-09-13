const TEAM_LABEL = { teamA: 'Team A', teamB: 'Team B' };

let state = window.RallyScoring.createGameState();
let pendingProposal = null;
let socket = null;

const scoreA = document.getElementById('score-teamA');
const scoreB = document.getElementById('score-teamB');
const serveA = document.getElementById('serve-teamA');
const serveB = document.getElementById('serve-teamB');
const proposalEl = document.getElementById('proposal');
const proposalText = document.getElementById('proposal-text');
const winnerEl = document.getElementById('winner-banner');
const statusCamera = document.getElementById('status-camera');
const statusVision = document.getElementById('status-vision');
const startCameraBtn = document.getElementById('btn-start-camera');
let cameraStarted = false;

function streamSocketUrl() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  if (location.port === '5500') {
    return protocol + '://' + location.hostname + ':8000/ws/stream';
  }
  return protocol + '://' + location.host + '/ws/stream';
}

function render() {
  scoreA.textContent = String(state.scores.teamA);
  scoreB.textContent = String(state.scores.teamB);
  serveA.classList.toggle('active', state.server === 'teamA' && !state.winner);
  serveB.classList.toggle('active', state.server === 'teamB' && !state.winner);
  if (state.winner) {
    winnerEl.hidden = false;
    winnerEl.textContent = TEAM_LABEL[state.winner] + ' wins \u2014 tap the centre dash to reset';
    hideProposal();
  } else {
    winnerEl.hidden = true;
  }
}

function hideProposal() {
  pendingProposal = null;
  proposalEl.hidden = true;
}

function showProposal(team) {
  if (state.winner) return;
  pendingProposal = team;
  proposalEl.hidden = false;
  proposalText.textContent = 'Vision suggests a point for ' + TEAM_LABEL[team] + '. Tap that side to confirm.';
}

function award(team) {
  if (state.winner) return;
  window.RallyScoring.awardPoint(state, team);
  hideProposal();
  render();
}

document.getElementById('btn-teamA').addEventListener('click', function () { award('teamA'); });
document.getElementById('btn-teamB').addEventListener('click', function () { award('teamB'); });
document.getElementById('proposal-dismiss').addEventListener('click', function (event) {
  event.stopPropagation();
  hideProposal();
});
document.querySelector('.divider').addEventListener('click', function () {
  if (state.winner) {
    state = window.RallyScoring.resetGame();
    hideProposal();
    render();
  }
});

function setCameraStatus(text) {
  if (statusCamera) statusCamera.textContent = text;
}
function setVisionStatus(text) {
  if (statusVision) statusVision.textContent = text;
}

function startCamera() {
  if (cameraStarted) return;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setCameraStatus('Camera API unavailable \u2014 use HTTPS or Chrome');
    return;
  }
  const video = document.getElementById('webcam');
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  setCameraStatus('Requesting camera\u2026');
  navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
    .then(function (mediaStream) {
      cameraStarted = true;
      if (startCameraBtn) startCameraBtn.classList.add('hidden');
      video.srcObject = mediaStream;
      video.muted = true;
      video.playsInline = true;
      video.play().catch(function () {});
      setCameraStatus('Camera live');
      video.onloadedmetadata = function () {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        setInterval(function () {
          if (!socket || socket.readyState !== WebSocket.OPEN) return;
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(function (blob) {
            if (blob && socket.readyState === WebSocket.OPEN) socket.send(blob);
          }, 'image/jpeg', 0.5);
        }, 100);
      };
    })
    .catch(function (err) {
      console.error('Error accessing camera: ', err);
      setCameraStatus('Camera blocked \u2014 tap the button, or use HTTPS');
      if (startCameraBtn) startCameraBtn.classList.remove('hidden');
    });
}

function connectVision() {
  setVisionStatus('Vision connecting\u2026');
  try {
    socket = new WebSocket(streamSocketUrl());
  } catch (err) {
    console.error('WebSocket error: ', err);
    setVisionStatus('Vision offline \u2014 scoring by tap still works');
    return;
  }
  socket.onopen = function () { setVisionStatus('Vision live'); };
  socket.onclose = function () { setVisionStatus('Vision offline \u2014 scoring by tap still works'); };
  socket.onmessage = function (event) {
    if (typeof event.data !== 'string') return;
    try {
      const message = JSON.parse(event.data);
      if (message.type === 'point_proposal' && (message.team === 'teamA' || message.team === 'teamB')) {
        showProposal(message.team);
      }
    } catch (err) {
      console.error('Invalid vision message: ', err);
    }
  };
  socket.onerror = function (err) {
    console.error('WebSocket error: ', err);
    setVisionStatus('Vision offline \u2014 scoring by tap still works');
  };
}

if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
render();
connectVision();
startCamera();
