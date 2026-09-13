#!/usr/bin/env python3
"""Fine-tune a YOLO nano detector on the prepared OpenTTGames YOLO dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
from shutil import copy2

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = ROOT / "models" / "ball_yolov8n.pt"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("/home/workdir/openttgames/yolo/openttgames.yaml"))
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out", type=Path, default=DEFAULT_WEIGHTS)
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.data.exists():
        raise SystemExit(f"Dataset yaml not found: {args.data}. Run prepare_openttgames.py first.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(args.out.parent / "runs"),
        name="openttgames-ball",
        exist_ok=True,
        patience=8,
        mosaic=0.5,
        close_mosaic=2,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        degrees=5,
        translate=0.05,
        scale=0.3,
        fliplr=0.5,
        workers=2,
    )
    best = args.out.parent / "runs" / "openttgames-ball" / "weights" / "best.pt"
    if best.exists():
        copy2(best, args.out)
        YOLO(str(best)).export(format="onnx", imgsz=args.imgsz, simplify=True)
        print(f"Saved fine-tuned weights to {args.out}")
    else:
        raise SystemExit("Training finished but best.pt was not written.")


if __name__ == "__main__":
    main()
