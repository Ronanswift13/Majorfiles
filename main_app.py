from __future__ import annotations

import argparse

from analyze_fusion_log import run_analysis
from fusion_record_demo import run_record_demo
from fusion_replay_demo import run_replay_demo
from fusion_ui_demo import run_ui
from fusion_demo import main as run_cli_demo  # existing CLI demo still uses main()
from test_fusion_logic import run_tests


def main() -> None:
    banner = (
        "Lidar/Vision Fusion Main App\n"
        "Modes:\n"
        "  ui      - start live Flet UI with LIDAR\n"
        "  record  - record fusion_log.csv\n"
        "  replay  - replay fusion_log.csv in console\n"
        "  analyze - print statistics from fusion_log.csv\n"
        "  cli     - run terminal fusion demo\n"
        "  test    - execute fusion self-tests\n"
    )
    print(banner)

    parser = argparse.ArgumentParser(description="Main launcher for fusion demos/tools.")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["ui", "record", "replay", "analyze", "cli", "test"],
        default="ui",
        help="Mode to launch (default: ui)",
    )
    args = parser.parse_args()

    if args.mode == "ui":
        run_ui()
    elif args.mode == "record":
        run_record_demo()
    elif args.mode == "replay":
        run_replay_demo()
    elif args.mode == "analyze":
        run_analysis()
    elif args.mode == "cli":
        run_cli_demo()
    elif args.mode == "test":
        print("Running fusion logic self-tests...")
        run_tests()
        print("All fusion tests passed ✅")


if __name__ == "__main__":
    main()
