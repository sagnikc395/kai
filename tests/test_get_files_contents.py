import pytest
from kai.get_file_content import get_file_content
from kai.config import FILE_MAX_CHARS


# happy path check
def test_reads_file(tmp_path):
    (tmp_path / "a.txt").write_text("hello")

    assert get_file_content(tmp_path, "a.txt") == "hello"


# error cases (parameterized)
@pytest.mark.parametrize(
    "path, error",
    [
        ("../x.txt", "not in the working dir"),
        ("missing.txt", "is not a file"),
        ("subdir", "is not a file"),
    ],
)
def test_invalid_paths(tmp_path, path, error):
    (tmp_path / "subdir").mkdir()

    result = get_file_content(tmp_path, path)

    assert error in result


# truncation behaviour
def test_truncates_large_file(tmp_path):
    (tmp_path / "big.txt").write_text("x" * FILE_MAX_CHARS)

    result = get_file_content(tmp_path, "big.txt")

    assert "truncated" in result


# exception while reading


def test_read_exception(tmp_path, monkeypatch):
    (tmp_path / "f.txt").write_text("data")

    monkeypatch.setattr(
        "builtins.open", lambda *a, **k: (_ for _ in ()).throw(IOError("boom"))
    )

    result = get_file_content(tmp_path, "f.txt")

    assert "Exception reading file" in result
