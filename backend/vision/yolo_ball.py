"""YOLO ball detector used by the RallyVision stream server."""

from __future__ import annotations

from pathlib import Path

DEFAULT_WEIGHTS = Path(__file__).resolve().parents[1] / "models" / "ball_yolov8n.pt"


class YoloBallDetector:
    def __init__(self, weights: Path | None = None, conf: float = 0.25):
        self.weights = Path(weights) if weights else DEFAULT_WEIGHTS
        self.conf = conf
        self._model = None

    @property
    def available(self) -> bool:
        return self.weights.exists()

    def _load(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(str(self.weights))
        return self._model

    def detect(self, frame, last_position=None):
        """Return (x, y, confidence) for the best ball, or None."""
        if not self.available:
            return None
        results = self._load()(frame, conf=self.conf, verbose=False)
        if not results:
            return None

        best = None
        best_score = -1.0
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                xyxy = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                cx = (xyxy[0] + xyxy[2]) / 2
                cy = (xyxy[1] + xyxy[3]) / 2
                score = confidence
                if last_position is not None:
                    dx = cx - last_position[0]
                    dy = cy - last_position[1]
                    score = confidence / (1.0 + (dx * dx + dy * dy) ** 0.5 / 50.0)
                if score > best_score:
                    best_score = score
                    best = (int(cx), int(cy), confidence)
        return best
