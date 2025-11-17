from __future__ import annotations

import subprocess
import sys
import textwrap

MENU_TEXT = textwrap.dedent(
    """
    === Lidar-Camera Fusion Launcher ===
    1) Live fusion (CLI)
    2) Live fusion UI
    3) Record fusion log to CSV
    4) Analyze existing fusion_log.csv
    5) Replay fusion_log.csv
    q) Quit
    """
)

SCRIPT_MAP = {
    "1": "fusion_demo.py",
    "2": "fusion_ui_demo.py",
    "3": "fusion_record_demo.py",
    "4": "analyze_fusion_log.py",
    "5": "fusion_replay_demo.py",
}


def run_script(script: str) -> None:
    print(f"\n[launcher] starting {script} ...\n")
    try:
        subprocess.run([sys.executable, script], check=False)
    except KeyboardInterrupt:
        print("\n[launcher] script interrupted by user\n")


def main() -> None:
    while True:
        print(MENU_TEXT)
        selection = input("Select mode: ").strip()

        if selection.lower() == "q":
            print("Exiting launcher.")
            break

        script = SCRIPT_MAP.get(selection)
        if script is None:
            print("Invalid selection, please try again.\n")
            continue

        run_script(script)


if __name__ == "__main__":
    main()
