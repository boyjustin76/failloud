# Contributing

Thanks for looking. This library has a narrow remit: **failures that do not raise.**

If you have hit one — a call that returns `False` instead of throwing, a path that
quietly becomes a different path, a window that reports itself visible while being
nowhere on screen — that is exactly what belongs here.

## What makes a good guard

1. **It is something you measured, not something you read.** Include the numbers: what
   you ran, on what, and what came back.
2. **It fails loudly.** Guards raise or return a value the caller must look at. They do
   not log a warning and continue.
3. **It does not act on the user's behalf.** This library reads, captures and reports.
   It does not close windows, delete files or retry.

## Adding one

- One file per job, named for the job. No `utils.py`, `helpers.py` or `common.py`.
- Public functions are typed and have a docstring that says **why** the code is shaped
  the way it is, not just what it does.
- Add the measurement to [`docs/traps.md`](docs/traps.md) with date and platform.
- Keep `failloud.fs` dependency-free and cross-platform. Platform-specific code goes
  under its own subpackage and raises a clear `ImportError` elsewhere.

## Tests

**Tests must run without any third-party application installed.** That is a hard rule —
otherwise nobody can verify your change.

Where the real target is an application, substitute something the test can create
itself. `tests/test_windows.py` spawns a standard `#32770` dialog through PowerShell,
which is the same window class Adobe's `alert()` uses, so the real code path is covered
with nothing installed.

Where a guard documents platform behaviour, **test the behaviour itself** — create the
directory with the trailing space and assert that Windows drops it. When the platform
changes, that test tells us before the documentation becomes wrong.

Mark platform-specific tests with `pytest.mark.skipif` and check occasionally with
`pytest -v` that they are actually running rather than quietly skipping.

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Examples

Anything non-obvious gets an entry in `examples/` that runs in one line with no
arguments. Use realistic shapes with harmless values. An example that needs setup before
it runs is not an example.

## Commits and pull requests

Describe what changed and what you verified. If you measured something, say what you
measured it on — platform, versions, numbers. If part of it is untested, say which part.
