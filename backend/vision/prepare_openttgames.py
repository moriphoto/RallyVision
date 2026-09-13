#!/usr/bin/env python3
"""Convert OpenTTGames ball_markup.json + videos into a YOLO detection dataset.

Official source: https://lab.osai.ai/
Ball labels are centres. This script wraps each visible centre in a square box
and writes Ultralytics YOLO TXT labels (class cx cy w h, all normalised).
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import cv2

BASE_URL = "https://lab.osai.ai/datasets/openttgames/data/"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=Path("/home/workdir/openttgames/annotations"))
    parser.add_argument("--videos", type=Path, default=Path("/home/workdir/openttgames/videos"))
    parser.add_argument("--out", type=Path, default=Path("/home/workdir/openttgames/yolo"))
    parser.add_argument("--box-px", type=int, default=32, help="Square box size around the ball centre.")
    parser.add_argument("--train", nargs="*", default=["test_2"])
    parser.add_argument("--val", nargs="*", default=["test_3"])
    return parser.parse_args()


def load_ball_markup(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as archive:
        return json.loads(archive.read("ball_markup.json"))


def visible_points(markup: dict) -> dict:
    points = {}
    for key, value in markup.items():
        if not isinstance(value, dict):
            continue
        x, y = int(value.get("x", -1)), int(value.get("y", -1))
        if x >= 0 and y >= 0:
            points[int(key)] = (x, y)
    return points


def write_yolo_label(path: Path, cx: int, cy: int, box_px: int, width: int, height: int) -> None:
    side = max(8, box_px)
    x1 = max(0, cx - side / 2)
    y1 = max(0, cy - side / 2)
    x2 = min(width, cx + side / 2)
    y2 = min(height, cy + side / 2)
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    ncx = ((x1 + x2) / 2) / width
    ncy = ((y1 + y2) / 2) / height
    path.write_text(f"0 {ncx:.6f} {ncy:.6f} {bw / width:.6f} {bh / height:.6f}\n")


def extract_clip(clip_id, zip_path, video_path, image_dir, label_dir, box_px):
    points = visible_points(load_ball_markup(zip_path))
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video {video_path}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    written = 0
    frame_idx = 0
    needed = set(points)
    last_needed = max(needed) if needed else -1
    while needed:
        ok, frame = capture.read()
        if not ok or frame is None or frame_idx > last_needed:
            break
        if frame_idx in needed:
            cx, cy = points[frame_idx]
            stem = f"{clip_id}_{frame_idx:06d}"
            cv2.imwrite(str(image_dir / f"{stem}.jpg"), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            write_yolo_label(label_dir / f"{stem}.txt", cx, cy, box_px, width, height)
            written += 1
            needed.remove(frame_idx)
        frame_idx += 1
    capture.release()
    return written


def write_data_yaml(out_dir: Path) -> Path:
    yaml_path = out_dir / "openttgames.yaml"
    yaml_path.write_text(
        "\n".join([f"path: {out_dir}", "train: images/train", "val: images/val", "names:", "  0: ball", ""])
    )
    return yaml_path


def main():
    args = parse_args()
    for split in ("train", "val"):
        (args.out / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.out / "labels" / split).mkdir(parents=True, exist_ok=True)
    totals = {}
    for split, clips in (("train", args.train), ("val", args.val)):
        count = 0
        for clip_id in clips:
            zip_path = args.annotations / f"{clip_id}.zip"
            video_path = args.videos / f"{clip_id}.mp4"
            if not zip_path.exists() or not video_path.exists():
                print(f"Skipping {clip_id}: missing file")
                continue
            written = extract_clip(clip_id, zip_path, video_path, args.out / "images" / split, args.out / "labels" / split, args.box_px)
            print(f"{split} {clip_id}: {written} labelled frames")
            count += written
        totals[split] = count
    yaml_path = write_data_yaml(args.out)
    print(f"Wrote {yaml_path} train={totals.get('train', 0)} val={totals.get('val', 0)}")
    print(f"Download remaining clips from {BASE_URL}")


if __name__ == "__main__":
    main()
