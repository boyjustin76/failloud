# failloud

**Desktop automation fails silently. This makes it fail loudly.**

[![tests](https://github.com/boyjustin76/failloud/actions/workflows/tests.yml/badge.svg)](https://github.com/boyjustin76/failloud/actions/workflows/tests.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Every bug in this library looked like success at the time:

- A frame extractor reported `extracted 142 frames`. There were zero files on disk.
- A capture of a failed job showed a splash screen. The dialog explaining the failure was
  a small window beside it, never recorded.
- An export wrote to `D:/exports ` and then every file written into it raised
  `FileNotFoundError` — while `os.path.exists("D:/exports ")` kept returning `True`.
- An automation run timed out after five minutes. The application had been sitting on a
  modal dialog the whole time, and nobody could say which one.

None of these raised. `failloud` is the set of guards that turn them into errors.

```bash
pip install git+https://github.com/boyjustin76/failloud          # core guards, no dependencies
pip install "failloud[capture] @ git+https://github.com/boyjustin76/failloud"  # + window capture
```

> Not on PyPI yet. Install from the repository until the first tagged release.

## Count what you wrote, don't trust what you were told

```python
from failloud.fs import write_bytes_checked, expect_file_count

for index, frame in enumerate(frames):
    write_bytes_checked(out_dir / f"{index:05d}.png", encode(frame))

expect_file_count(out_dir, "*.png", len(frames))   # raises if the writes lied
```

`cv2.imwrite()` cannot write to a non-ASCII path on Windows. It does not raise — it
returns `False`. Encode in memory and let Python write the bytes, then count them back.

## Read the dialog that froze your automation

```python
from failloud.windows import find_modal, capture_window

modal = find_modal("Illustrator")
if modal:
    print(modal.message)      # "Script Alert  OK  The file could not be saved."
    capture_window("fail.png", hwnd=modal.window.hwnd)
```

A COM or scripting call stops dead when the application raises a dialog — no return
value, no exception. Read it *before* you kill the process.

It is often said that Adobe's dialogs cannot be inspected. That is true of UI
Automation, which reports one opaque container. Plain Win32 `EnumChildWindows` returns
the title and body text just fine.

## Capture windows that are not on screen

```python
from failloud.windows import capture_window, capture_all

capture_window("app.png", proc="AfterFX")     # works while occluded
capture_all("evidence/", proc="AfterFX")      # every window, when the cause is unknown
```

`PrintWindow(PW_RENDERFULLCONTENT)` asks the window to render itself, so it works when
the window is covered, on another virtual desktop, or off-screen — without stealing
focus or disturbing the user.

Do not use `Process.MainWindowHandle` to find the window. Illustrator returns a bogus
**160x28** handle for it; capturing that yields a blank sliver. Enumerating top-level
windows and taking the largest returns the real **1900x1012** window.

## Stop hard-coding paths

```python
from failloud.fs import find_ancestor_dir, safe_join

workspace = find_ancestor_dir(["lab/work", "work"], env_var="WORK_DIR")
target = safe_join(workspace, user_supplied_name, "output.png")
```

`safe_join` cleans **every** segment, not just the last one — the segment that breaks is
the one used as a parent directory.

## What this library will not do

**It never closes a window.** Synthetic keystrokes leak into whatever has focus, and
coordinate clicks assume a screen size, a DPI scale and a z-order. A misplaced click
once launched an unrelated application. Read it, capture it, log it, and tell a human.

## Scope

| Module | Platform | Dependencies |
|---|---|---|
| `failloud.fs` | any | none |
| `failloud.windows` | Windows | Pillow |

`failloud.windows` raises `ImportError` with an explanation on other platforms, so the
filesystem guards stay usable everywhere.

## Development

```bash
git clone https://github.com/boyjustin76/failloud
cd failloud
pip install -e ".[dev]"
pytest                                        # no external applications required
python examples/verified_batch_write.py
python examples/read_blocking_dialog.py       # spawns its own dialog to demonstrate
```

The Windows tests spawn a standard `#32770` dialog through PowerShell — the same window
class Adobe's `alert()` uses — so they exercise the real code paths without needing any
third-party software installed.

Every claim in [`docs/traps.md`](docs/traps.md) has a test. If Windows or a library ever
changes, the test fails before the documentation becomes a lie.

## See also

- [`docs/traps.md`](docs/traps.md) — the measurements behind each guard
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to add one
- [한국어 설명](README.ko.md)

MIT licensed.
