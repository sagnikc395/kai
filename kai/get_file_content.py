import os

from .config import FILE_MAX_CHARS


def _is_within_directory(root: str, target: str) -> bool:
    try:
        return os.path.commonpath([root, target]) == root
    except ValueError:
        return False


def get_file_content(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not _is_within_directory(abs_working_dir, abs_file_path):
        return f"Error: '{file_path}' is not in the working dir"
    if not os.path.isfile(abs_file_path):
        return f"Error: '{file_path}' is not a file"

    try:
        with open(abs_file_path, "r", encoding="utf-8") as f:
            file_content_string = f.read(FILE_MAX_CHARS)
            if len(file_content_string) >= FILE_MAX_CHARS:
                # truncate so we save on tokens
                file_content_string += (
                    f'[...File "{file_path}" truncated at {FILE_MAX_CHARS} chars.]'
                )
        return file_content_string
    except Exception as e:
        return f"Exception reading file: {e}"
