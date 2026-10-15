"""Find a directory by walking up from where you are, instead of hard-coding its path.

An absolute path in a config file is a time bomb: the day someone reorganises the tree,
every tool that referenced it dies at once, usually with an error that points at the
wrong thing. Searching upwards by name survives the move.

Why the default depth is 11
    Tools that run inside git worktrees sit a few levels deeper than the same tools run
    from a normal checkout. A depth of 8 was not enough; 11 covers it with room to
    spare. Callers can set whatever they need.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DEPTH = 11


def find_ancestor_dir(
    names: str | list[str],
    start: str | Path | None = None,
    depth: int = DEFAULT_DEPTH,
    env_var: str | None = None,
) -> Path | None:
    """Walk up from ``start`` looking for the first of ``names`` that exists.

    Lookup order:

    1. ``env_var``, if set and the path exists - an explicit override always wins.
    2. ``start`` and up to ``depth`` of its ancestors, trying each name in order.

    A name may contain ``/`` to match a nested path, for example ``"lab/work"``.

    Returns ``None`` rather than raising, so the caller can decide whether to create the
    directory, prompt, or fall back.
    """
    if isinstance(names, str):
        names = [names]

    if env_var:
        override = os.environ.get(env_var)
        if override and Path(override).exists():
            return Path(override).resolve()

    here = Path(start or Path.cwd()).resolve()
    for _ in range(depth):
        for name in names:
            candidate = here.joinpath(*str(name).replace("\\", "/").split("/"))
            if candidate.exists():
                return candidate.resolve()
        if here.parent == here:  # reached the filesystem root
            break
        here = here.parent
    return None


def require_ancestor_dir(
    names: str | list[str],
    start: str | Path | None = None,
    depth: int = DEFAULT_DEPTH,
    env_var: str | None = None,
    hint: str = "",
) -> Path:
    """Like :func:`find_ancestor_dir`, but raise a message that says how to fix it.

    The error names what was searched for, where the search started, and which
    environment variable would override it - so the person reading the traceback can act
    without reading the source.
    """
    found = find_ancestor_dir(names, start=start, depth=depth, env_var=env_var)
    if found:
        return found

    wanted = " or ".join(str(name) for name in ([names] if isinstance(names, str) else names))
    origin = Path(start or Path.cwd()).resolve()
    message = f"could not find {wanted} (searched up {depth} levels from {origin})"
    if env_var:
        message += f"\n  set {env_var} to point at it directly"
    if hint:
        message += f"\n  {hint}"
    raise FileNotFoundError(message)
