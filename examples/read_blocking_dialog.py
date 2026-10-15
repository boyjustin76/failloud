"""Find the dialog that froze an application, read it, and capture it.

Run it with no arguments and it spawns its own dialog so you can see the output
immediately:

    python examples/read_blocking_dialog.py
    python examples/read_blocking_dialog.py --proc Illustrator --out out/

The only input this example needs is a process name. Nothing is hard-coded.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from failloud.windows import capture_all, capture_window, find_modal  # noqa: E402

DEMO_TITLE = "failloud demo"
DEMO_BODY = "Scratch disk is full."


def _spawn_demo_dialog() -> subprocess.Popen:
    """A stand-in for a real application dialog: fake text, real window class."""
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.MessageBox]::Show('{DEMO_BODY}','{DEMO_TITLE}')"
    )
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-STA", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proc", help="process name without extension; omit for a demo")
    parser.add_argument("--out", default="out", help="where to write captures")
    args = parser.parse_args()

    demo = None
    proc = args.proc
    if not proc:
        demo = _spawn_demo_dialog()
        proc = "powershell"
        time.sleep(2.0)

    try:
        modal = find_modal(proc)
        if not modal:
            print(f"{proc}: nothing is blocking it. Capturing every window instead.")
            for path, window in capture_all(args.out, proc=proc, stem="window"):
                print(f"  {window.class_name:<24} {window.width}x{window.height}  {path}")
            return 2

        print(f"class     : {modal.window.class_name}")
        print(f"size      : {modal.window.width}x{modal.window.height}")
        print(f"blocking  : {modal.blocked}")
        print(f"text      : {modal.message or '(empty - owner-drawn, look at the image)'}")

        shot = capture_window(Path(args.out) / "modal.png", hwnd=modal.window.hwnd)
        print(f"capture   : {shot}")
        print("\nThe dialog was left open. This library never closes windows.")
        return 0
    finally:
        if demo:  # only ever kill the process this example started
            demo.kill()
            demo.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
