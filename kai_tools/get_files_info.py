import os


def get_files_info(working_directory, directory=None):
    abs_working_dir = os.path.abspath(working_directory)
    if directory is None:
        directory = abs_working_dir
    abs_directory = os.path.abspath(os.path.join(working_directory, directory))

    if not abs_directory.startswith(abs_working_dir):
        # the abs directory would be outside
        # error message as string helpful for the LLM to understand
        return f"Error: {directory} is not a directory"

    final_response = ""
    contents = os.listdir(abs_directory)
    for content in contents:
        content_path = os.path.join(abs_directory, content)
        is_dir = os.path.isdir(os.path.join(content_path))
        size = os.path.getsize(content_path)
        final_response += f"- {content}: file_size={size} bytes, is_dir={is_dir}\n"
    return final_response
