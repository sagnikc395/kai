import os

from .config import FILE_MAX_CHARS


def get_file_content(working_directory, file_path):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f"Error: '{file_path}' is not in the working dir"
    if not os.path.isfile(abs_file_path):
        return f"Error: '{file_path}' is not a file"

    file_content_string = ""
    try:
        with open(abs_file_path, "r") as f:
            file_content_string = f.read(FILE_MAX_CHARS)
            if len(file_content_string) >= FILE_MAX_CHARS:
                # truncate that , so we save on tokens
                file_content_string += (
                    f'[...File "{file_path}" truncated at 10000 chars.]'
                )
        return file_content_string
    except Exception as e:
        return f"Exception reading file: {e}"
