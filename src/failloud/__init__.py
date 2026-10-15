"""failloud - make silent failures in desktop automation loud.

Two groups of guards, built from bugs that all looked like success:

``failloud.fs``
    Cross-platform. Path names Windows rewrites behind your back, directories found by
    name instead of hard-coded, and writes that are counted back off disk.

``failloud.windows``
    Windows only, imported on demand so the rest stays portable. Find the dialog that
    froze your automation, read its text, and capture it even when it is hidden.

Typical use::

    from failloud.fs import expect_file_count, write_bytes_checked

    for index, frame in enumerate(frames):
        write_bytes_checked(out_dir / f"{index:05d}.png", encode(frame))
    expect_file_count(out_dir, "*.png", len(frames))   # raises if the writes lied
"""

from .fs import (
    NameReport,
    WriteNotVerified,
    check_name,
    count_on_disk,
    expect_file_count,
    find_ancestor_dir,
    require_ancestor_dir,
    safe_join,
    safe_name,
    safe_parts,
    write_bytes_checked,
    write_text_checked,
)

__version__ = "0.1.0"

__all__ = [
    "NameReport",
    "WriteNotVerified",
    "__version__",
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
