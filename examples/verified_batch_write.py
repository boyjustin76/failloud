"""Write a batch of files and prove on disk that they are there.

    python examples/verified_batch_write.py
    python examples/verified_batch_write.py --out "D:/exports " --count 5

Try passing an ``--out`` that ends in a space. Without cleaning, that is the case where
a directory is created under a different name and every later write into it fails.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from failloud.fs import (  # noqa: E402
    WriteNotVerified,
    check_name,
    expect_file_count,
    safe_join,
    write_bytes_checked,
)

# Smallest valid 1x1 PNG, so the example writes real files without any dependency.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6300010000050001"
    "0d0a2db40000000049454e44ae426082"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="target directory")
    parser.add_argument("--count", type=int, default=3, help="how many files to write")
    args = parser.parse_args()

    out = args.out or str(Path(tempfile.mkdtemp(prefix="failloud-")) / "exports ")

    report = check_name(Path(out).name)
    print(f"requested name : {report.given!r}")
    print(f"name on disk   : {report.stored!r}")
    if report.changed:
        print(f"  ! the name changes; breaks when used as a parent: {report.breaks_as_parent}")

    written = 0
    for index in range(args.count):
        write_bytes_checked(safe_join(out, f"{index:05d}.png"), TINY_PNG)
        written += 1

    folder = Path(safe_join(out))
    try:
        on_disk = expect_file_count(folder, "*.png", written)
    except WriteNotVerified as error:
        print(f"\nFAILED: {error}")
        return 1

    print(f"\nwrote to       : {folder}")
    print(f"OK: intended {written}, found {on_disk} on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
