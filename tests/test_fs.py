"""Tests for the filesystem guards. No external applications, no network.

Several tests create real files to check that the behaviour documented in the modules is
still true. If Windows or OpenCV ever changes, these fail first and tell us.
"""

from __future__ import annotations

import sys

import pytest

from failloud.fs import (
    WriteNotVerified,
    check_name,
    count_on_disk,
    expect_file_count,
    find_ancestor_dir,
    require_ancestor_dir,
    safe_join,
    safe_name,
    write_bytes_checked,
    write_text_checked,
)

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="Windows naming rules")


# --- name rules ---------------------------------------------------------------


@pytest.mark.parametrize(
    "given, expected",
    [
        ("report ", "report"),
        ("data...", "data"),
        ("both . ", "both"),
        (" leading kept", " leading kept"),
        ("inner space kept", "inner space kept"),
        ("ordinary", "ordinary"),
    ],
)
def test_safe_name_strips_only_the_tail(given: str, expected: str) -> None:
    assert safe_name(given) == expected


def test_safe_join_cleans_every_segment_not_only_the_last() -> None:
    joined = safe_join("base", "trailing ", "file.txt")
    assert "trailing " not in joined
    assert joined.endswith("file.txt")


def test_safe_join_leaves_a_drive_root_alone() -> None:
    assert safe_join("C:\\", "data", "file.txt").startswith("C:\\")


def test_check_name_reports_without_changing_anything() -> None:
    space = check_name("folder ")
    assert space.changed and space.breaks_as_parent and not space.ok
    assert space.stored == "folder"

    dot = check_name("folder.")
    assert dot.changed and not dot.breaks_as_parent  # a dot still works as a parent

    assert check_name("folder").ok


@windows_only
def test_windows_really_strips_a_trailing_space_from_directories(tmp_path) -> None:
    (tmp_path / "trailing ").mkdir()
    assert (tmp_path / "trailing").is_dir(), "Windows drops the trailing space"
    assert (tmp_path / "trailing ").exists(), "yet the original name still reports True"

    with pytest.raises(FileNotFoundError):
        (tmp_path / "trailing " / "inner.txt").write_text("x", encoding="utf-8")

    write_bytes_checked(safe_join(str(tmp_path), "trailing ", "inner.txt"), b"x")


@windows_only
def test_a_trailing_dot_renames_but_still_works_as_a_parent(tmp_path) -> None:
    (tmp_path / "dotted.").mkdir()
    assert (tmp_path / "dotted").is_dir()
    (tmp_path / "dotted." / "inner.txt").write_text("x", encoding="utf-8")
    assert (tmp_path / "dotted" / "inner.txt").exists()


# --- finding directories ------------------------------------------------------


def test_find_ancestor_dir_walks_up(tmp_path) -> None:
    (tmp_path / "workspace").mkdir()
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert find_ancestor_dir("workspace", start=deep) == (tmp_path / "workspace").resolve()


def test_first_matching_name_wins(tmp_path) -> None:
    (tmp_path / "second").mkdir()
    assert find_ancestor_dir(["first", "second"], start=tmp_path).name == "second"


def test_names_may_contain_a_sub_path(tmp_path) -> None:
    (tmp_path / "lab" / "work").mkdir(parents=True)
    assert find_ancestor_dir("lab/work", start=tmp_path).name == "work"


def test_env_var_overrides_the_search(tmp_path, monkeypatch) -> None:
    (tmp_path / "workspace").mkdir()
    (tmp_path / "explicit").mkdir()
    monkeypatch.setenv("FAILLOUD_TEST_DIR", str(tmp_path / "explicit"))
    found = find_ancestor_dir("workspace", start=tmp_path, env_var="FAILLOUD_TEST_DIR")
    assert found.name == "explicit"


def test_depth_limit_is_honoured(tmp_path) -> None:
    (tmp_path / "workspace").mkdir()
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    assert find_ancestor_dir("workspace", start=deep, depth=2) is None


def test_missing_directory_returns_none_and_require_explains(tmp_path) -> None:
    assert find_ancestor_dir("nowhere", start=tmp_path) is None
    with pytest.raises(FileNotFoundError) as error:
        require_ancestor_dir(
            "nowhere", start=tmp_path, env_var="FAILLOUD_TEST_DIR", hint="or pass it in config"
        )
    assert "FAILLOUD_TEST_DIR" in str(error.value)
    assert "or pass it in config" in str(error.value)


# --- checked writes -----------------------------------------------------------


def test_write_bytes_checked_creates_parents_and_round_trips(tmp_path) -> None:
    path = write_bytes_checked(tmp_path / "new" / "image.png", b"\x89PNG....")
    assert path.exists() and path.read_bytes().startswith(b"\x89PNG")


def test_write_text_checked_bom_flag(tmp_path) -> None:
    plain = write_text_checked(tmp_path / "config.json", '{"a": 1}')
    assert not plain.read_bytes().startswith(b"\xef\xbb\xbf")

    with_bom = write_text_checked(tmp_path / "script.ps1", "Write-Host 'ok'", bom=True)
    assert with_bom.read_bytes().startswith(b"\xef\xbb\xbf")


def test_an_empty_write_is_caught(tmp_path) -> None:
    with pytest.raises(WriteNotVerified):
        write_bytes_checked(tmp_path / "empty.png", b"", min_size=1)


def test_expect_file_count_catches_the_silent_miss(tmp_path) -> None:
    for index in range(3):
        write_bytes_checked(tmp_path / f"{index}.png", b"x")
    assert expect_file_count(tmp_path, "*.png", 3) == 3
    assert count_on_disk(tmp_path, "*.png") == 3

    with pytest.raises(WriteNotVerified) as error:
        expect_file_count(tmp_path, "*.png", 142)
    assert "142" in str(error.value) and "3" in str(error.value)


@windows_only
def test_cv2_imwrite_fails_silently_on_a_non_ascii_path(tmp_path) -> None:
    """The bug this package exists for: a library that returns False instead of raising."""
    cv2 = pytest.importorskip("cv2")
    numpy = pytest.importorskip("numpy")

    directory = tmp_path / "\ud55c\uae00\ud3f4\ub354"  # Korean directory name
    directory.mkdir()
    image = numpy.zeros((8, 8, 3), dtype=numpy.uint8)
    target = directory / "image.png"

    if cv2.imwrite(str(target), image) and target.exists():
        pytest.skip("this OpenCV build handles non-ASCII paths; the trap is fixed")

    assert not target.exists(), "imwrite reported failure but produced a file"

    encoded, buffer = cv2.imencode(".png", image)
    assert encoded
    write_bytes_checked(target, buffer.tobytes())
    assert target.exists(), "encode-in-memory then write must succeed"
