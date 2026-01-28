import pytest
from kai.get_files_info import get_files_info


def index_by_name(results):
    return {r[0]: r for r in results}


@pytest.mark.parametrize(
    "args,expected",
    [
        (
            ("calculator",),
            {
                ".gitignore": False,
                "tests.py": False,
                "main.py": False,
                "pkg": True,
            },
        ),
        (
            ("calculator", "pkg"),
            {
                "render.py": False,
                "__pycache__": True,
                "calculator.py": False,
            },
        ),
    ],
)
def test_get_files_info(args, expected):
    result = get_files_info(*args)
    files = index_by_name(result)

    # same set of files
    assert set(files.keys()) == set(expected.keys())

    for name, is_dir in expected.items():
        entry = files[name]
        entry_name, file_size, entry_is_dir = entry
        assert entry_name == name
        assert isinstance(file_size, int)
        assert file_size >= 0
        assert entry_is_dir is is_dir


def assert_valid_entry(entry, *, name, is_dir):
    assert entry["name"] == name
    assert isinstance(entry["file_size"], int)
    assert entry["file_size"] >= 0
    assert entry["is_dir"] is is_dir
