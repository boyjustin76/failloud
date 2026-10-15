"""Windows guards: find, read and capture the window that stopped your automation.

- :mod:`~failloud.windows.top_windows` - enumerate real top-level windows
- :mod:`~failloud.windows.modal_window` - find the blocking dialog and read its text
- :mod:`~failloud.windows.window_capture` - capture a window even when it is occluded

Nothing here closes a window. Synthetic keystrokes leak into whatever has focus, and
coordinate clicks assume a screen size, a DPI scale and a z-order. Read it, capture it,
log it, and tell a human.

Windows only. Importing this package elsewhere raises :class:`ImportError` with a
message that says why.
"""

import sys

if sys.platform != "win32":
    raise ImportError(
        "failloud.windows requires Windows: it calls Win32 EnumWindows and PrintWindow. "
        f"Current platform: {sys.platform}. The failloud.fs guards are cross-platform."
    )

from .modal_window import DIALOG_CLASS, Modal, find_modal, is_blocked, read_child_texts
from .top_windows import Window, largest_window, list_top_windows, process_name, window_text
from .window_capture import capture_all, capture_window, grab, window_is_up

__all__ = [
    "DIALOG_CLASS",
    "Modal",
    "Window",
    "capture_all",
    "capture_window",
    "find_modal",
    "grab",
    "is_blocked",
    "largest_window",
    "list_top_windows",
    "process_name",
    "read_child_texts",
    "window_is_up",
    "window_text",
]
