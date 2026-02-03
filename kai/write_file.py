import os


def _is_within_directory(root: str, target: str) -> bool:
    try:
        return os.path.commonpath([root, target]) == root
    except ValueError:
        return False


def write_file(working_directory, file_path, content):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not _is_within_directory(abs_working_dir, abs_file_path):
        return f"Error: '{file_path}' is not in the working directory"
    parent_dir = os.path.dirname(abs_file_path)

    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            return f"Could not create parent dirs: {parent_dir} = {e}"
    try:
        with open(abs_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return (
            f"Successfully wrote to '{file_path}' ({len(content)} characters written)"
        )
    except Exception as e:
        return f"Failed to write to file : {file_path}, {e}"
