from fastapi import FastAPI, WebSocket
import cv2
import numpy as np

app = FastAPI()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # Convert received bytes to numpy array
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                # Here you will integrate your bounce detection logic
                pass

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
