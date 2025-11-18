#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live LiDAR zone demo: streams real measurements with zone tracking feedback."""

from __future__ import annotations

import time

from new_lidar import get_lidar_distance_cm, NewLidarError
from lidar_zone_logic import (
    CabinetZone,
    LidarZoneTracker,
    LidarStatus,
    LidarDecision,
)


POLL_INTERVAL_S = 0.2


def build_tracker() -> tuple[LidarZoneTracker, set[int]]:
    """Create the tracker and default authorized cabinet set."""

    zones = [
        CabinetZone(1, 1.05, 1.95),   # cabinet 1: center 1.50 m, width 0.90 m
        CabinetZone(2, 1.95, 2.85),   # cabinet 2: center 2.40 m, width 0.90 m
        CabinetZone(3, 3.405, 4.305), # cabinet 3: center 3.855 m, width 0.90 m (after 0.555 m gap)
        CabinetZone(4, 4.305, 5.205), # cabinet 4: center 4.755 m, width 0.90 m
        CabinetZone(5, 5.205, 6.105), # cabinet 5: center 5.655 m, width 0.90 m
    ]
    tracker = LidarZoneTracker(
        zones=zones,
        movement_threshold_m=0.20,
        static_threshold_m=0.08,
        static_window_s=2.0,
        walk_window_s=1.5,
    )
    authorized = {1, 3}
    return tracker, authorized


def format_decision(decision: LidarDecision) -> str:
    idx = decision.cabinet_index if decision.cabinet_index is not None else "-"
    if decision.distance_m is None:
        dist_text = "None"
    else:
        dist_text = f"{decision.distance_m * 100.0:.1f} cm"
    return (
        f"[zone_live] dist={dist_text} | cabinet={idx} | status={decision.status.name} | "
        f"safe={decision.is_safe} | reason={decision.reason}"
    )


def main() -> None:
    tracker, authorized = build_tracker()
    print("Starting lidar_zone_live_demo... Press Ctrl+C to stop.")

    try:
        while True:
            try:
                distance_cm = get_lidar_distance_cm()
            except NewLidarError as exc:
                decision = tracker.update(None, authorized_cabinets=authorized)
                print(f"{format_decision(decision)} | sensor_error={exc}")
                time.sleep(POLL_INTERVAL_S)
                continue

            if distance_cm is None:
                decision = tracker.update(None, authorized_cabinets=authorized)
            else:
                distance_m = distance_cm / 100.0
                decision = tracker.update(distance_m, authorized_cabinets=authorized)

            print(format_decision(decision))
            time.sleep(POLL_INTERVAL_S)
    except KeyboardInterrupt:
        print("\nStopping lidar_zone_live_demo...")


if __name__ == "__main__":
    main()
