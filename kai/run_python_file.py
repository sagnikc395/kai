import os
import subprocess
import sys


def _is_within_directory(root: str, target: str) -> bool:
    try:
        return os.path.commonpath([root, target]) == root
    except ValueError:
        return False


def run_python_file(working_directory: str, file_path: str, args=None):
    if args is None:
        args = []
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not _is_within_directory(abs_working_dir, abs_file_path):
        return f"Error : {file_path} is not in the working dir"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file."
    if not file_path.endswith(".py"):
        return f"Error: {file_path} is not a Python file."

    try:
        final_args = [sys.executable, file_path]
        final_args.extend(args)
        output = subprocess.run(
            final_args,
            timeout=30,
            cwd=abs_working_dir,
            capture_output=True,
            text=True,
        )
        if output.stdout == "" and output.stderr == "":
            final_string = "No output produced.\n"
        else:
            final_string = f"STDOUT: {output.stdout}\nSTDERR: {output.stderr}\n"

        if output.returncode != 0:
            final_string += f"Process exited with code {output.returncode}"

        return final_string
    except Exception as e:
        return f"Error: executing Python file: {e}"
