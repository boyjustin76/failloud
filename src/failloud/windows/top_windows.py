"""Enumerate the visible top-level windows a process actually owns.

Everything else in ``failloud.windows`` stands on this module.

Why not ``Process.MainWindowHandle``?
    Because it lies. Adobe Illustrator returned a **160x28** handle for its main window
    (measured 2026-09-21, Windows 11). Capturing that handle yields a blank sliver, and
    nothing raises. Picking the largest visible top-level window of the same process
    returned the real **1900x1012** window.

Injecting your own values
    Process and title filters are arguments. No application name is hard-coded here.
"""

from __future__ import annotations

import contextlib
import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

# Keep coordinates honest on high-DPI displays. Already set, or an older Windows: fine.
with contextlib.suppress(Exception):
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

#: Window class of a standard Windows dialog box. Adobe ``alert()`` boxes use it too.
DIALOG_CLASS = "#32770"


@dataclass(frozen=True)
class Window:
    """One visible top-level window."""

    hwnd: int
    class_name: str
    title: str
    width: int
    height: int
    enabled: bool
    """``False`` means something is blocking input to this window - usually a modal."""

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_dialog(self) -> bool:
        return self.class_name == DIALOG_CLASS


def process_name(pid: int) -> str:
    """PID to executable name without extension. Empty string if access is denied."""
    handle = _kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        buffer = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(512)
        if _kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return buffer.value.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        return ""
    finally:
        _kernel32.CloseHandle(handle)


def window_text(hwnd: int) -> str:
    """Title bar text of a window, or the caption of a child control."""
    length = _user32.GetWindowTextLengthW(hwnd)
    if not length:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def window_class(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def _client_size(hwnd: int) -> tuple[int, int]:
    rect = wintypes.RECT()
    _user32.GetClientRect(hwnd, ctypes.byref(rect))
    return rect.right - rect.left, rect.bottom - rect.top


def list_top_windows(
    proc: str | None = None,
    title: str | None = None,
    min_area: int = 0,
) -> list[Window]:
    """Visible top-level windows matching the filters, largest first.

    Args:
        proc: Executable name without extension, case-insensitive.
        title: Substring of the window title, case-insensitive.
        min_area: Drop windows smaller than this, in pixels. ``40000`` (200x200) is a
            practical cut-off for ignoring toolbars and floating palettes.
    """
    found: list[Window] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _collect(hwnd: int, _: int) -> bool:
        if not _user32.IsWindowVisible(hwnd):
            return True
        width, height = _client_size(hwnd)
        if width * height < min_area:
            return True
        if title and title.lower() not in window_text(hwnd).lower():
            return True
        if proc:
            pid = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if process_name(pid.value).lower() != proc.lower():
                return True
        found.append(
            Window(
                hwnd=hwnd,
                class_name=window_class(hwnd),
                title=window_text(hwnd),
                width=width,
                height=height,
                enabled=bool(_user32.IsWindowEnabled(hwnd)),
            )
        )
        return True

    _user32.EnumWindows(_collect, 0)
    found.sort(key=lambda window: -window.area)
    return found


def largest_window(
    proc: str | None = None,
    title: str | None = None,
    min_area: int = 40000,
) -> Window | None:
    """The biggest matching window, or ``None``.

    Use this instead of ``MainWindowHandle``. See the module docstring for why.
    """
    windows = list_top_windows(proc=proc, title=title, min_area=min_area)
    return windows[0] if windows else None
