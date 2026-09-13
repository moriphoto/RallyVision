const socket = new WebSocket('ws://localhost:8000/ws/stream');

socket.onopen = () => {
  const video = document.getElementById('webcam');
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');

  navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    .then(stream => {
      video.srcObject = stream;
      video.onloadedmetadata = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        setInterval(() => {
          context.drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(blob => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(blob);
            }
          }, 'image/jpeg', 0.5);
        }, 100);
      };
    })
    .catch(err => console.error("Error accessing camera: ", err));
};
