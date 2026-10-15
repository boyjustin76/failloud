"""Capture a window even when it is hidden behind other windows.

Why not a screenshot?
    Because an occluded window is simply not in the screenshot. We have had windows
    report ``IsWindowVisible() == True`` while being nowhere on screen, which makes a
    full-screen grab useless as evidence. ``PrintWindow`` with
    ``PW_RENDERFULLCONTENT`` asks the window to render itself, so it works when the
    window is covered, on another virtual desktop, or off-screen - and it never steals
    focus or disturbs what the user is doing.

Capture every window, not just the biggest one
    A failure once produced a single screenshot of a splash screen, while the small
    dialog beside it - the actual cause - was never recorded. When you do not yet know
    what went wrong, use :func:`capture_all`.
"""

from __future__ import annotations

import ctypes
from pathlib import Path

from PIL import Image

from .top_windows import Window, largest_window, list_top_windows

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 2


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


def grab(hwnd: int, width: int, height: int) -> Image.Image:
    """Render one window into a PIL image. Saving is the caller's business."""
    window_dc = _user32.GetWindowDC(hwnd)
    memory_dc = _gdi32.CreateCompatibleDC(window_dc)
    bitmap = _gdi32.CreateCompatibleBitmap(window_dc, width, height)
    _gdi32.SelectObject(memory_dc, bitmap)
    try:
        _user32.PrintWindow(hwnd, memory_dc, PW_RENDERFULLCONTENT)
        header = _BitmapInfoHeader()
        header.biSize = ctypes.sizeof(_BitmapInfoHeader)
        header.biWidth, header.biHeight = width, -height  # negative: top-down rows
        header.biPlanes, header.biBitCount, header.biCompression = 1, 32, 0
        buffer = ctypes.create_string_buffer(width * height * 4)
        _gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(header), 0)
        return Image.frombuffer("RGB", (width, height), buffer, "raw", "BGRX", 0, 1)
    finally:
        _gdi32.DeleteObject(bitmap)
        _gdi32.DeleteDC(memory_dc)
        _user32.ReleaseDC(hwnd, window_dc)


def capture_window(
    out: str | Path,
    *,
    proc: str | None = None,
    title: str | None = None,
    hwnd: int | None = None,
    min_area: int = 40000,
) -> Path | None:
    """Save one window to ``out``.

    Returns the path, or ``None`` when no matching window exists - so the caller can
    fall back to a full-screen grab instead of crashing.
    """
    if hwnd is None:
        found = largest_window(proc=proc, title=title, min_area=min_area)
        if not found:
            return None
        hwnd, width, height = found.hwnd, found.width, found.height
    else:
        window = next((w for w in list_top_windows() if w.hwnd == hwnd), None)
        if not window:
            return None
        width, height = window.width, window.height

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    grab(hwnd, width, height).save(out)
    return out


def capture_all(
    out_dir: str | Path,
    *,
    proc: str,
    stem: str = "window",
    min_area: int = 0,
) -> list[tuple[Path, Window]]:
    """Save every visible window of ``proc``, for when the cause is still unknown.

    One window that fails to render does not abort the rest.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shots: list[tuple[Path, Window]] = []
    for index, window in enumerate(list_top_windows(proc=proc, min_area=min_area), 1):
        path = out_dir / f"{stem}_{index:02d}.png"
        try:
            grab(window.hwnd, window.width, window.height).save(path)
        except Exception:  # noqa: BLE001 - one bad window must not lose the others
            continue
        shots.append((path, window))
    return shots


def window_is_up(proc: str, min_area: int = 40000) -> bool:
    """Whether a real window exists yet, without capturing anything.

    Useful while waiting for a heavyweight application to finish starting.
    """
    return largest_window(proc=proc, min_area=min_area) is not None
