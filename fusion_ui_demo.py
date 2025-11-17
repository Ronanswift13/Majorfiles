from __future__ import annotations

import threading
import time
from datetime import datetime

import flet as ft

from lidar_tof import get_lidar_distance
from vision_logic import VisionState, LinePosition, BodyOrientation, GestureCode
from fusion_logic import fuse_sensors


def build_dummy_vision() -> VisionState:
    """与 fusion_demo.py 相同的固定 VisionState。"""

    return VisionState(
        person_present=True,
        line_position=LinePosition.BEYOND_LINE,
        orientation=BodyOrientation.FACING_CABINET,
        gesture=GestureCode.NONE,
        timestamp=datetime.now(),
    )


def main(page: ft.Page) -> None:
    page.title = "Fusion UI Demo"

    title_text = ft.Text("Fusion Monitor", size=24, weight=ft.FontWeight.BOLD)
    distance_text = ft.Text("distance: --", size=20)
    warning_text = ft.Text("warning: SAFE", size=22, weight=ft.FontWeight.BOLD)
    log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)

    page.add(
        ft.Column(
            [
                title_text,
                distance_text,
                warning_text,
                ft.Text("Event log:"),
                log_view,
            ],
            expand=True,
        )
    )

    vision_state = build_dummy_vision()

    def update_loop() -> None:
        while True:
            distance = get_lidar_distance()
            fused = fuse_sensors(distance, vision_state)

            if fused.distance_cm is None:
                distance_text.value = "distance: None"
            else:
                distance_text.value = f"distance: {fused.distance_cm:.1f} cm"

            warning_text.value = f"warning: {fused.warning_level}"
            if fused.warning_level == "SAFE":
                warning_text.color = ft.colors.GREEN
            elif fused.warning_level == "CAUTION":
                warning_text.color = ft.colors.AMBER
            else:
                warning_text.color = ft.colors.RED

            log_line = ft.Text(
                f"[{fused.timestamp.strftime('%H:%M:%S')}] dist={fused.distance_cm} cm | warning={fused.warning_level}"
            )
            log_view.controls.append(log_line)
            if len(log_view.controls) > 50:
                del log_view.controls[0]

            page.update()
            time.sleep(0.5)

    threading.Thread(target=update_loop, daemon=True).start()


if __name__ == "__main__":
    ft.app(target=main)
