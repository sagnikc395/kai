import os
import tempfile

from kai.tools.edit import EditTool
from kai.tools.glob_ import GlobTool
from kai.tools.grep_ import GrepTool
from kai.tools.read import ReadTool
from kai.tools.write import WriteTool


def test_read_write_edit_tools():
    os.environ["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "notes", "todo.txt")

        write_result = WriteTool().call(
            {
                "file_path": file_path,
                "content": "alpha\nbeta\nalpha",
            }
        )
        assert not write_result.is_error, f"write failed: {write_result.output}"

        read_result = ReadTool().call(
            {
                "file_path": file_path,
                "offset": 2,
                "limit": 1,
            }
        )
        assert not read_result.is_error, f"read failed: {read_result.output}"
        assert "2\tbeta" in read_result.output, (
            f"read output missing numbered line: {read_result.output}"
        )

        duplicate_edit = EditTool().call(
            {
                "file_path": file_path,
                "old_string": "alpha",
                "new_string": "gamma",
                "replace_all": False,
            }
        )
        assert duplicate_edit.is_error, "expected duplicate edit to fail"

        edit_result = EditTool().call(
            {
                "file_path": file_path,
                "old_string": "alpha",
                "new_string": "gamma",
                "replace_all": True,
            }
        )
        assert not edit_result.is_error, f"edit failed: {edit_result.output}"

        with open(file_path) as f:
            content = f.read()
        assert content == "gamma\nbeta\ngamma", (
            f"unexpected edited content: {content!r}"
        )


def test_glob_and_grep_tools():
    os.environ["NO_COLOR"] = "1"
    with tempfile.TemporaryDirectory() as temp_dir:
        _must_write(os.path.join(temp_dir, "a.go"), "package main\n")
        nested_dir = os.path.join(temp_dir, "nested")
        _must_write(
            os.path.join(nested_dir, "b.go"), "package nested\nfunc Target() {}\n"
        )
        _must_write(os.path.join(nested_dir, "b.txt"), "Target in text\n")

        glob_result = GlobTool().call(
            {
                "pattern": "**/*.go",
                "path": temp_dir,
            }
        )
        assert not glob_result.is_error, f"glob failed: {glob_result.output}"
        assert os.path.join(temp_dir, "a.go") in glob_result.output
        assert os.path.join(temp_dir, "nested", "b.go") in glob_result.output

        grep_result = GrepTool().call(
            {
                "pattern": "Target",
                "path": temp_dir,
                "include": "*.go",
            }
        )
        assert not grep_result.is_error, f"grep failed: {grep_result.output}"
        assert "b.go:2:func Target() {}" in grep_result.output, (
            f"grep output missing expected match: {grep_result.output}"
        )
        assert "b.txt" not in grep_result.output, (
            f"grep include filter did not exclude txt file: {grep_result.output}"
        )


def _must_write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
