"""Turn a pytest JUnit report into a GitHub step summary.

A green check mark does not tell you whether a test ran or was skipped. The Windows
guards need a desktop session to exercise a real dialog, and CI runners vary - so the
run page should say out loud how many tests actually executed, and why the rest did not.

    pytest --junitxml=report.xml
    python .github/ci_summary.py report.xml >> $GITHUB_STEP_SUMMARY
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: ci_summary.py <report.xml>", file=sys.stderr)
        return 2

    report = Path(argv[1])
    if not report.exists():
        print(f"### Test summary\n\nNo report at `{report}` - pytest did not get that far.")
        return 0

    cases = ElementTree.parse(report).getroot().iter("testcase")
    passed: list[str] = []
    skipped: list[tuple[str, str]] = []
    failed: list[str] = []

    for case in cases:
        name = f"{case.get('classname', '')}::{case.get('name', '')}".lstrip(":")
        skip = case.find("skipped")
        if skip is not None:
            skipped.append((name, skip.get("message", "").strip()))
        elif case.find("failure") is not None or case.find("error") is not None:
            failed.append(name)
        else:
            passed.append(name)

    # A workflow notice shows on the run page and stays readable through the public API,
    # so the counts can be checked without opening the logs.
    counts = f"{len(passed)} passed, {len(skipped)} skipped, {len(failed)} failed"
    print(f"::notice title=Test summary::{counts}", file=sys.stderr)
    for name, reason in skipped:
        print(f"::notice title=Skipped::{name} - {reason or 'no reason given'}", file=sys.stderr)

    print("### Test summary\n")
    print("| passed | skipped | failed |\n|---|---|---|")
    print(f"| {len(passed)} | {len(skipped)} | {len(failed)} |\n")

    if skipped:
        print("<details><summary>Skipped tests and why</summary>\n")
        for name, reason in skipped:
            print(f"- `{name}` - {reason or 'no reason given'}")
        print("\n</details>")
    else:
        print("Every collected test ran. Nothing was skipped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
