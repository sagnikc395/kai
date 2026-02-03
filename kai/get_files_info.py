import os


def _is_within_directory(root: str, target: str) -> bool:
    try:
        return os.path.commonpath([root, target]) == root
    except ValueError:
        return False


def get_files_info(working_directory, directory="."):
    abs_working_dir = os.path.abspath(working_directory)
    if directory is None:
        abs_directory = abs_working_dir
    else:
        abs_directory = os.path.abspath(os.path.join(working_directory, directory))

    if not _is_within_directory(abs_working_dir, abs_directory):
        return f"Error: {directory} is not a directory"
    if not os.path.isdir(abs_directory):
        return f"Error: {directory} is not a directory"

    entries = []
    for name in os.listdir(abs_directory):
        content_path = os.path.join(abs_directory, name)
        is_dir = os.path.isdir(content_path)
        size = os.path.getsize(content_path)
        entries.append((name, size, is_dir))
    return entries
