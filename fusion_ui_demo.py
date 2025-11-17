from __future__ import annotations

import csv
import threading
import time
from datetime import datetime
from pathlib import Path

import flet as ft

from fusion_logic import fuse_sensors
from lidar_tof import get_lidar_distance
from vision_logic import BodyOrientation, GestureCode, LinePosition, VisionState


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

    placeholder_src = "data:image/gif;base64,R0lGODlhAQABAAAAACw="
    image_view = ft.Image(width=320, height=240, fit=ft.ImageFit.CONTAIN, src=placeholder_src)
    placeholder_text = ft.Text(
        "No camera frame (frame_base64 is None)",
        size=14,
        text_align=ft.TextAlign.CENTER,
        weight=ft.FontWeight.BOLD,
    )
    image_container = ft.Container(
        width=320,
        height=240,
        bgcolor=ft.colors.GREY_200,
        content=ft.Stack(
            [
                image_view,
                ft.Container(content=placeholder_text, alignment=ft.alignment.center),
            ],
            expand=True,
        ),
    )

    record_state = {"enabled": False}

    def on_record_toggle(e: ft.ControlEvent) -> None:
        record_state["enabled"] = bool(e.control.value)
        page.update()

    record_switch = ft.Checkbox(label="Record to fusion_log.csv", value=False, on_change=on_record_toggle)

    page.add(
        ft.Column(
            [
                title_text,
                distance_text,
                warning_text,
                record_switch,
                image_container,
                ft.Text("Event log:"),
                log_view,
            ],
            expand=True,
        )
    )

    vision_state = build_dummy_vision()
    csv_path = Path(__file__).with_name("fusion_log.csv")

    def append_csv_row(vision_snapshot: VisionState, fusion_snapshot) -> None:
        file_exists = csv_path.exists()
        with csv_path.open("a", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            if not file_exists:
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
            writer.writerow(
                [
                    fusion_snapshot.timestamp.isoformat(),
                    fusion_snapshot.distance_cm,
                    vision_snapshot.person_present,
                    vision_snapshot.line_position.name,
                    vision_snapshot.orientation.name,
                    vision_snapshot.gesture.name,
                    fusion_snapshot.too_close,
                    fusion_snapshot.warning_level,
                ]
            )

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

            frame_b64 = getattr(fused.vision, "frame_base64", None)
            if frame_b64:
                image_view.src_base64 = frame_b64
                image_view.src = None
                placeholder_text.visible = False
            else:
                image_view.src_base64 = None
                image_view.src = placeholder_src
                placeholder_text.visible = True

            if record_state["enabled"]:
                append_csv_row(fused.vision, fused)

            page.update()
            time.sleep(0.5)

    threading.Thread(target=update_loop, daemon=True).start()


def run_ui() -> None:
    ft.app(target=main)


if __name__ == "__main__":
    run_ui()
