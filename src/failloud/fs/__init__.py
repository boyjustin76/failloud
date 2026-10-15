"""Filesystem guards: the places where the filesystem lies to you quietly.

- :mod:`~failloud.fs.name_rules` - Windows rewrites names ending in a space or a dot
- :mod:`~failloud.fs.ancestor_dir` - find directories by name instead of hard-coding paths
- :mod:`~failloud.fs.checked_write` - confirm what you wrote actually landed

Works on any platform. A few of the tests only make sense on Windows and skip elsewhere.
"""

from .ancestor_dir import DEFAULT_DEPTH, find_ancestor_dir, require_ancestor_dir
from .checked_write import (
    WriteNotVerified,
    count_on_disk,
    expect_file_count,
    write_bytes_checked,
    write_text_checked,
)
from .name_rules import NameReport, check_name, safe_join, safe_name, safe_parts

__all__ = [
    "DEFAULT_DEPTH",
    "NameReport",
    "WriteNotVerified",
    "check_name",
    "count_on_disk",
    "expect_file_count",
    "find_ancestor_dir",
    "require_ancestor_dir",
    "safe_join",
    "safe_name",
    "safe_parts",
    "write_bytes_checked",
    "write_text_checked",
]
