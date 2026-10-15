"""Tests for the Windows guards, with no third-party application involved.

A standard Windows dialog (``#32770``) is spawned by the test itself through
PowerShell's ``MessageBox``. That is the same window class Adobe's ``alert()`` uses, so
finding it, reading it and capturing it exercises the real code paths.

The spawned process is killed to clean up. No synthetic keystrokes, no coordinate
clicks - those leak into whatever else is on screen.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only")

if sys.platform == "win32":
    from failloud.windows import (
        DIALOG_CLASS,
        capture_all,
        capture_window,
        find_modal,
        largest_window,
        list_top_windows,
        window_is_up,
    )

TITLE = "failloud test dialog"
BODY = "Scratch disk is full."


@pytest.fixture()
def message_box():
    """Spawn one standard dialog, then kill only the process we started."""
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        f"[System.Windows.Forms.MessageBox]::Show('{BODY}','{TITLE}')"
    )
    process = subprocess.Popen(
        ["powershell", "-NoProfile", "-STA", "-Command", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):  # up to 10 seconds
            if any(w.title == TITLE for w in list_top_windows(min_area=0)):
                break
            time.sleep(0.1)
        else:
            process.kill()
            pytest.skip("dialog never appeared (headless session?)")
        yield process
    finally:
        process.kill()
        process.wait(timeout=10)


def _our_dialog():
    return next(w for w in list_top_windows(min_area=0) if w.title == TITLE)


def test_dialog_uses_the_standard_class(message_box) -> None:
    dialog = _our_dialog()
    assert dialog.class_name == DIALOG_CLASS
    assert dialog.is_dialog


def test_modal_text_is_readable(message_box) -> None:
    """Win32 reads dialog text that UI Automation reports as an opaque container."""
    modal = find_modal("powershell")
    assert modal is not None, "the spawned dialog was not found"
    assert TITLE in modal.message
    assert BODY in modal.message, f"body text was not read: {modal.texts}"


def test_capture_writes_a_real_image(message_box, tmp_path) -> None:
    from PIL import Image

    dialog = _our_dialog()
    out = capture_window(tmp_path / "dialog.png", hwnd=dialog.hwnd)
    assert out is not None and out.exists()

    image = Image.open(out)
    assert image.size == (dialog.width, dialog.height)
    colours = image.convert("RGB").getcolors(maxcolors=1 << 24) or []
    assert len(colours) > 2, "a single-colour image means nothing was rendered"


def test_capture_all_keeps_every_window(message_box, tmp_path) -> None:
    shots = capture_all(tmp_path, proc="powershell", min_area=0)
    assert shots, "no window was captured"
    assert all(path.exists() for path, _ in shots)
    assert any(window.title == TITLE for _, window in shots)


def test_an_absent_process_returns_none_rather_than_raising(tmp_path) -> None:
    """Callers must be able to fall back instead of crashing."""
    missing = "failloud-no-such-process"
    assert largest_window(proc=missing) is None
    assert window_is_up(missing) is False
    assert capture_window(tmp_path / "none.png", proc=missing) is None
    assert find_modal(missing) is None
