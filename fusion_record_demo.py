from __future__ import annotations

import csv
import os
import time
from datetime import datetime

from lidar_tof import get_lidar_distance
from vision_logic import VisionState, LinePosition, BodyOrientation, GestureCode
from fusion_logic import fuse_sensors


def build_dummy_vision() -> VisionState:
    return VisionState(
        person_present=True,
        line_position=LinePosition.BEYOND_LINE,
        orientation=BodyOrientation.FACING_CABINET,
        gesture=GestureCode.NONE,
        timestamp=datetime.now(),
    )


def main() -> None:
    csv_path = "fusion_log.csv"

    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "timestamp_iso",
                    "distance_cm",
                    "person_present",
                    "line_position",
                    "orientation",
                    "gesture",
                    "too_close",
                    "warning_level",
                ]
            )

    while True:
        distance = get_lidar_distance()
        vision = build_dummy_vision()
        fused = fuse_sensors(distance, vision)

        with open(csv_path, "a", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    fused.timestamp.isoformat(),
                    fused.distance_cm,
                    vision.person_present,
                    vision.line_position.name,
                    vision.orientation.name,
                    vision.gesture.name,
                    fused.too_close,
                    fused.warning_level,
                ]
            )

        print(
            f"[record] {fused.timestamp} dist={fused.distance_cm} cm | "
            f"too_close={fused.too_close} | warning={fused.warning_level}"
        )
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nfusion_record_demo stopped by user")
