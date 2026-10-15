"""Write a file, then read the directory back and count. Never trust "it worked".

The motivating bug
    ``cv2.imwrite()`` cannot write to a path containing non-ASCII characters on Windows.
    It does not raise - it returns ``False``. Code that ignores the return value happily
    reports "extracted 142 frames" and leaves nothing on disk. A ``.json`` written next
    to them with ``pathlib`` survives, so you get folders full of metadata and no images,
    which reads like a deletion rather than a failed write.

    Measured 2026-09-28 on Windows 11 with OpenCV 5.0.0.

    The fix is to encode in memory (``cv2.imencode``) and let Python write the bytes,
    then verify the count.

The family of bugs this belongs to
    Every one of them looked like success: a request for three indicators that silently
    applied one, a "moved to date X" log line next to a screenshot of date Y. The common
    thread is never reading the result back.
"""

from __future__ import annotations

from pathlib import Path


class WriteNotVerified(RuntimeError):
    """A write reported success but could not be confirmed on disk."""


def write_bytes_checked(path: str | Path, data: bytes, *, min_size: int = 1) -> Path:
    """Write bytes, create parents, then stat the file to confirm it exists.

    Python writes the bytes itself, so non-ASCII paths are not a problem.

    Raises:
        WriteNotVerified: if the file is missing or smaller than ``min_size``.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if not path.exists():
        raise WriteNotVerified(f"file is missing after writing it: {path}")
    size = path.stat().st_size
    if size < min_size:
        raise WriteNotVerified(f"file is too small ({size} < {min_size} bytes): {path}")
    return path


def write_text_checked(
    path: str | Path,
    text: str,
    *,
    encoding: str = "utf-8",
    bom: bool = False,
) -> Path:
    """Write text and read it back to confirm the bytes round-trip.

    Pass ``bom=True`` to prepend a UTF-8 BOM. Windows PowerShell 5.1 decodes a BOM-less
    ``.ps1`` as the system ANSI code page, which corrupts non-ASCII source and produces
    parse errors like ``The string is missing the terminator: "``. The opposite is also
    true elsewhere - Adobe ExtendScript fails to read JSON that starts with a BOM - so
    the choice stays with the caller.
    """
    data = text.encode(encoding)
    if bom and encoding.lower().replace("-", "") == "utf8":
        data = b"\xef\xbb\xbf" + data
    written = write_bytes_checked(path, data)
    if written.read_bytes() != data:
        raise WriteNotVerified(f"contents differ after writing: {written}")
    return written


def expect_file_count(directory: str | Path, pattern: str, expected: int) -> int:
    """Count files on disk and compare with what you believe you wrote.

    One call at the end of a batch is what turns "extracted 142 frames" into an error
    instead of a lie.

    Raises:
        WriteNotVerified: if the counts differ.
    """
    found = count_on_disk(directory, pattern)
    if found != expected:
        raise WriteNotVerified(
            f"expected {expected} file(s) matching {pattern!r} in {directory}, found {found}"
        )
    return found


def count_on_disk(directory: str | Path, pattern: str) -> int:
    """Count matching files without raising."""
    return len(list(Path(directory).glob(pattern)))
