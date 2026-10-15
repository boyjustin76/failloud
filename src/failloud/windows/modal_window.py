"""Find the dialog that froze your automation, and read what it says.

A COM or scripting automation stops dead the moment the application raises a dialog.
No return value, no exception - the call simply never comes back. If you do not know
what the dialog said, all you get is a timeout.

So read it **before** you kill the process.

Yes, the text is readable
    It is often claimed that Adobe's dialogs cannot be inspected. That is true of UI
    Automation, which reports a single opaque container. Plain Win32
    ``EnumChildWindows`` + ``GetWindowTextW`` returns the title and the body just fine.

    Applications that paint their chrome entirely themselves have no child windows, so
    the text comes back empty. That is what :func:`failloud.windows.capture_window` is
    for - keep both, always.

This module never closes anything
    There is no dismiss helper here and there will not be one. Synthetic keystrokes leak
    into whatever window has focus, and coordinate clicks assume a screen size, a DPI
    scale and a z-order. A misplaced click once launched an unrelated application.
    Read it, capture it, log it, and tell a human.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
from dataclasses import dataclass, field

from .top_windows import DIALOG_CLASS, Window, list_top_windows, window_text

_user32 = ctypes.windll.user32


@dataclass(frozen=True)
class Modal:
    """A dialog that is blocking a process, plus whatever text could be read from it."""

    window: Window
    texts: list[str] = field(default_factory=list)
    """Captions of the dialog's child controls. Empty for owner-drawn dialogs."""
    main_window: Window | None = None
    """The largest window of the same process, for context."""
    blocked: bool = False
    """``True`` when the main window is disabled - proof that something is blocking it."""

    @property
    def message(self) -> str:
        """Title and child captions joined into one line, ready to log or classify."""
        return " ".join([self.window.title, *self.texts]).strip()


def read_child_texts(hwnd: int) -> list[str]:
    """Captions of every child control of a window.

    Returns an empty list for owner-drawn dialogs - that is information, not an error.
    """
    texts: list[str] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def _collect(child: int, _: int) -> bool:
        caption = window_text(child).strip()
        if caption:
            texts.append(caption)
        return True

    _user32.EnumChildWindows(hwnd, _collect, 0)
    return texts


def find_modal(proc: str) -> Modal | None:
    """The dialog blocking ``proc``, or ``None`` if nothing is blocking it.

    Selection order:

    1. A window whose class is ``#32770`` - the standard Windows dialog class.
    2. Otherwise, if the largest window is **disabled**, the next largest window is the
       candidate. Owner-drawn dialogs show up here.
    """
    windows = list_top_windows(proc=proc)  # largest first
    if not windows:
        return None
    main = windows[0]

    for window in windows:
        if window.is_dialog:
            return Modal(
                window=window,
                texts=read_child_texts(window.hwnd),
                main_window=main,
                blocked=not main.enabled,
            )

    if not main.enabled and len(windows) > 1:
        candidate = windows[1]
        return Modal(
            window=candidate,
            texts=read_child_texts(candidate.hwnd),
            main_window=main,
            blocked=True,
        )

    return None


def is_blocked(proc: str) -> bool:
    """Whether the process's main window is disabled, without picking a dialog.

    Cheap enough for a pre-flight check before you hand an application more work.
    """
    windows = list_top_windows(proc=proc)
    return bool(windows) and not windows[0].enabled


__all__ = ["DIALOG_CLASS", "Modal", "find_modal", "is_blocked", "read_child_texts"]
