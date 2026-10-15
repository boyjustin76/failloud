"""Windows silently rewrites names that end in a space or a dot.

Measured on Windows 11, Python 3.11:

==================  ====================================  ==========================
Name ends with      As a directory                        As a file
==================  ====================================  ==========================
space ``"a "``      created as ``a``. **Using it as a      saved as ``a``. The name
                    parent raises FileNotFoundError.**    just quietly differs.
                    ``exists("a ")`` still returns True.
dot ``"a."``        created as ``a``. Using it as a        saved as ``a``. The name
                    parent works fine.                     just quietly differs.
==================  ====================================  ==========================

Only one of those four cases raises. The other three change the name on disk while your
variable still holds the original, which breaks any later lookup by name - and nothing
tells you. The case that does raise says ``FileNotFoundError`` without hinting that a
trailing space is involved, and GUI applications are even less helpful: Illustrator
reports only ``Error: the operation was cancelled``.

The fix is to clean **every** path segment, not just the last one, because the segment
that breaks is the one used as a parent. Do not verify with ``exists()`` - a directory
name with a trailing space reports ``True``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

_TRAILING = re.compile(r"[ .]+$")
_ROOT = re.compile(r"[A-Za-z]:[\\/]?$")


def safe_name(name: str) -> str:
    """Strip trailing spaces and dots from a single path segment.

    >>> safe_name("report ")
    'report'
    >>> safe_name("data...")
    'data'
    >>> safe_name(" leading space is kept")
    ' leading space is kept'
    """
    return _TRAILING.sub("", str(name))


def safe_parts(*parts: str) -> list[str]:
    """Clean every segment and drop the ones that become empty."""
    return [cleaned for cleaned in (safe_name(part) for part in parts) if cleaned]


def safe_join(*parts: str) -> str:
    """Join path segments, cleaning **each** of them.

    Cleaning only the final segment is not enough: the segment that breaks is the one
    used as a parent directory. Drive letters and roots are left alone.
    """
    if not parts:
        return ""
    head = str(parts[0])
    if not (head in ("/", "\\") or _ROOT.match(head)):
        head = safe_name(head)
    return os.path.join(head, *safe_parts(*parts[1:]))


@dataclass(frozen=True)
class NameReport:
    """What Windows will actually do with a name."""

    given: str
    stored: str
    """The name that will exist on disk."""
    changed: bool
    """Whether the stored name differs from the one you asked for."""
    breaks_as_parent: bool
    """Whether using this name as a parent directory will raise."""

    @property
    def ok(self) -> bool:
        return not self.changed


def check_name(name: str) -> NameReport:
    """Report what a name will do, without changing it.

    Lets the caller decide between rejecting the input and cleaning it.
    """
    stored = safe_name(name)
    return NameReport(
        given=name,
        stored=stored,
        changed=stored != name,
        breaks_as_parent=name.endswith(" "),  # only a trailing space breaks as a parent
    )
