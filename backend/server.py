from pathlib import Path
import sys

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent))
from vision.yolo_ball import YoloBallDetector

app = FastAPI()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
YOLO_DETECTOR = YoloBallDetector()

# Image Y increases downwards.
Y_HISTORY_LIMIT = 30
MIN_BALL_AREA = 20
MAX_BALL_AREA = 8000
BOUNCE_COOLDOWN_FRAMES = 20


def detect_bounce(y_coords):
    if len(y_coords) < 3:
        return False
    dy1 = y_coords[-2] - y_coords[-3]
    dy2 = y_coords[-1] - y_coords[-2]
    return dy1 > 0 and dy2 <= 0


def get_scoring_side(ball_x, table_center_x):
    return 'teamA' if ball_x < table_center_x else 'teamB'


def _color_mask(hsv):
    white = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 60, 255]))
    orange = cv2.inRange(hsv, np.array([5, 80, 80]), np.array([25, 255, 255]))
    mask = cv2.bitwise_or(white, orange)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def track_ball(frame, last_position=None):
    """Return (ball_x, ball_y) from the current frame, or None if not found."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = _color_mask(hsv)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_BALL_AREA or area > MAX_BALL_AREA:
            continue
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        if circularity < 0.55:
            continue
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            continue
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        score = circularity * area
        if last_position is not None:
            dx = cx - last_position[0]
            dy = cy - last_position[1]
            score /= 1.0 + np.hypot(dx, dy) / 50.0
        candidates.append((score, cx, cy))

    if not candidates:
        return None

    _, ball_x, ball_y = max(candidates, key=lambda item: item[0])
    return int(ball_x), int(ball_y)


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    y_coords = []
    last_position = None
    cooldown = 0
    table_center_x = 320

    try:
        while True:
            data = await websocket.receive_bytes()
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                table_center_x = frame.shape[1] // 2
                yolo_hit = YOLO_DETECTOR.detect(frame, last_position) if YOLO_DETECTOR.available else None
                if yolo_hit is not None:
                    tracked = (yolo_hit[0], yolo_hit[1])
                else:
                    tracked = track_ball(frame, last_position)

                if tracked is None:
                    if cooldown > 0:
                        cooldown -= 1
                    continue

                ball_x, ball_y = tracked
                last_position = (ball_x, ball_y)
                y_coords.append(ball_y)
                if len(y_coords) > Y_HISTORY_LIMIT:
                    y_coords = y_coords[-Y_HISTORY_LIMIT:]

                if cooldown > 0:
                    cooldown -= 1
                    continue

                if detect_bounce(y_coords):
                    scoring_team = get_scoring_side(ball_x, table_center_x)
                    print(f"Bounce detected! Proposing point for {scoring_team}")
                    await websocket.send_json({
                        "type": "point_proposal",
                        "team": scoring_team,
                        "ball": {"x": ball_x, "y": ball_y},
                    })
                    y_coords = []
                    cooldown = BOUNCE_COOLDOWN_FRAMES

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
