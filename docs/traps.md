# Traps

Each entry is something that actually happened, with the measurement that pinned it
down and the guard that now catches it. Every claim here has a test — if the platform
changes, the test fails before this page becomes a lie.

---

## 1. Windows silently rewrites names ending in a space or a dot

**Guard** `failloud.fs.name_rules` · **Measured** Windows 11, Python 3.11

| Name ends with | As a directory | As a file |
|---|---|---|
| space `"a "` | created as `a`. **Using it as a parent raises `FileNotFoundError`.** Yet `exists("a ")` returns `True` | saved as `a`; the name quietly differs |
| dot `"a."` | created as `a`. Using it as a parent works | saved as `a`; the name quietly differs |

Only one of those four cases raises. The other three leave your variable holding a name
that is not on disk, which breaks any later lookup by name — silently.

The case that *does* raise is still unhelpful: `FileNotFoundError` gives no hint that a
trailing space is involved. GUI applications are worse. Adobe Illustrator reports only
`Error: the operation was cancelled`, which is indistinguishable from a dozen other
problems.

**Fix** — clean every path segment, not just the last. Do not verify with `exists()`.

---

## 2. `cv2.imwrite` fails silently on non-ASCII paths

**Guard** `failloud.fs.checked_write` · **Measured** 2026-09-28, Windows 11, OpenCV 5.0.0

Writing to a path containing non-ASCII characters returns `False` and writes nothing. No
exception. A loop that ignores the return value reports `extracted 142 frames` and
leaves an empty directory.

It is worse than a plain failure because a `.json` written beside the images with
`pathlib` survives — so you get directories full of metadata and no images, which looks
like something deleted them.

**Fix** — `cv2.imencode` into memory, let Python write the bytes, then
`expect_file_count()` at the end of the batch.

**The family this belongs to.** Every related bug looked like success: a request for
three indicators that silently applied one, a "moved to date X" log line sitting next to
a screenshot of date Y. The common thread is never reading the result back.

---

## 3. `MainWindowHandle` returns the wrong window

**Guard** `failloud.windows.top_windows` · **Measured** 2026-09-21, Windows 11, Adobe Illustrator

`Process.MainWindowHandle` returned a **160x28** handle. Capturing it produced a blank
sliver, and nothing raised. Enumerating visible top-level windows of the same process and
taking the largest returned the real **1900x1012** window.

**Fix** — `largest_window(proc=...)`.

Trying the same thing from PowerShell with `Add-Type -MemberDefinition` fails to compile
over a `System.Drawing.Rectangle` reference, which is why this lives in Python.

---

## 4. A screenshot does not contain an occluded window

**Guard** `failloud.windows.window_capture` · **Measured** 2026-09-21, Windows 11

Windows reported `IsWindowVisible() == True` while being nowhere in a full-screen grab,
because another window covered them. The saved evidence was useless.

`PrintWindow(hwnd, hdc, PW_RENDERFULLCONTENT)` asks the window to render itself.
Measured: return value 1, 958x1030, 707 distinct colours — a real image, not a blank
buffer. A minimised application has no window to find, so the call returns `None` and the
caller can fall back.

**Capture everything when the cause is unknown.** One failure produced a single capture
of a splash screen while the small dialog beside it — the actual cause — went unrecorded.

---

## 5. Adobe dialog text *is* readable — just not through UI Automation

**Guard** `failloud.windows.modal_window` · **Measured** 2026-09-21, Illustrator 30.8.1

The common claim is that Adobe's dialogs cannot be inspected. That is true of UI
Automation: `FindAll(Descendants)` returns a single opaque container. Plain Win32 works.

```
class  #32770 · 420x159 · 2 child controls
title  "Script Alert"
text   ["OK", "This window was raised by a test."]
main window: IsWindowEnabled = False
```

Applications that paint their chrome entirely themselves have no child windows, so the
text comes back empty — that is information, not an error. Keep the text *and* the
image, always.

---

## 6. Do not try to dismiss the dialog

**Guard** none — there is deliberately no dismiss helper in this library

- Synthetic keystrokes leak into whatever window has focus. With an IME active they can
  be swallowed entirely.
- Coordinate clicks assume a screen size, a DPI scale and a z-order. A misplaced click
  once launched an unrelated application.

**Fix** — read, capture, log, and tell a human. Blocking and reporting is cheaper than
acting on the user's behalf and being wrong.

---

## 7. PowerShell 5.1 decodes BOM-less `.ps1` as the ANSI code page

**Guard** `failloud.fs.checked_write` (`write_text_checked(..., bom=True)`) · **Measured** 2026-09-21

A `.ps1` file containing non-ASCII text, saved as UTF-8 without a BOM, failed with
`The string is missing the terminator: "`. The file was fine; the decoding corrupted the
characters and swallowed a quote.

The opposite is true elsewhere — Adobe ExtendScript fails to read JSON that begins with a
BOM. The two rules point in opposite directions, so the caller chooses.
