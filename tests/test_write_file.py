import pytest
from kai.write_file import write_file


# happy path and nested directories
@pytest.mark.parametrize(
    "file_path, content",
    [
        ("a.txt", "hello"),
        ("subdir/nested.txt", "nested content"),
    ],
)
def test_write_file_success(tmp_path, file_path, content):
    file_path_obj = tmp_path / file_path

    result = write_file(tmp_path, str(file_path_obj), content)

    assert "Successfully wrote" in result
    assert file_path_obj.read_text() == content


# path outside working directory
def test_write_file_outside_working_dir(tmp_path):
    result = write_file(tmp_path, "../outside.txt", "nope")
    assert "not in the working directory" in result


# exception (parameterize with monkeypatch)
@pytest.mark.parametrize(
    "patch_target, expected_msg, exc_msg",
    [
        ("os.makedirs", "Could not create parent dirs", "boom"),
        ("builtins.open", "Failed to write to file", "write failed"),
    ],
)
def test_write_file_exceptions(
    tmp_path, monkeypatch, patch_target, expected_msg, exc_msg
):
    file_path = tmp_path / "subdir/f.txt"

    def fail(*args, **kwargs):
        raise OSError(exc_msg) if "makedirs" in patch_target else IOError(exc_msg)

    monkeypatch.setattr(patch_target, fail)

    result = write_file(tmp_path, str(file_path), "data")
    assert expected_msg in result
    assert exc_msg in result
