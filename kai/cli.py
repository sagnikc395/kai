import os

import click
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .get_file_content import get_file_content
from .get_files_info import get_files_info
from .run_python_file import run_python_file
from .write_file import write_file


DEFAULT_MODEL = "gemini-3-flash-preview"


def _resolve_working_dir(ctx, param, value):
    return os.path.abspath(value)


def _format_files_info(result):
    if isinstance(result, str):
        return result
    lines = []
    for name, size, is_dir in result:
        lines.append(f"- {name}: file_size={size} bytes, is_dir={is_dir}")
    return "\n".join(lines)


def _get_api_key():
    load_dotenv()
    return os.environ.get("GEMINI_API_KEY")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--working-dir",
    default=".",
    show_default=True,
    callback=_resolve_working_dir,
    help="Base directory for file utilities.",
)
@click.pass_context
def cli(ctx, working_dir):
    ctx.ensure_object(dict)
    ctx.obj["working_dir"] = working_dir


@cli.command("chat")
@click.argument("prompt")
@click.option("--debug", is_flag=True, help="Print Debug Information (API KEY)")
@click.option("--verbose", is_flag=True, help="Print verbose execution details")
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="Gemini model name.",
)
def chat(prompt, debug, verbose, model):
    api_key = _get_api_key()
    if api_key is None:
        raise click.ClickException("Please set GEMINI_API_KEY in your environment.")

    if debug:
        click.echo(f"[DEBUG] API Key: {api_key}")

    client = genai.Client(api_key=api_key)
    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]

    response = client.models.generate_content(model=model, contents=messages)
    if response is None or response.usage_metadata is None:
        raise click.ClickException("Response is malformed")

    click.echo(response.text)
    if verbose:
        click.echo(f"User prompt: {prompt}\n")
        click.echo(f"Prompt tokens : {response.usage_metadata.prompt_token_count}\n")
        click.echo(
            f"Response tokens: {response.usage_metadata.candidates_token_count}\n"
        )


@cli.command("list-files")
@click.argument("directory", required=False, default=".")
@click.pass_context
def list_files(ctx, directory):
    working_dir = ctx.obj["working_dir"]
    click.echo(_format_files_info(get_files_info(working_dir, directory)))


@cli.command("read-file")
@click.argument("file_path")
@click.pass_context
def read_file(ctx, file_path):
    working_dir = ctx.obj["working_dir"]
    click.echo(get_file_content(working_dir, file_path))


@cli.command("write-file")
@click.argument("file_path")
@click.option("--content", required=True, help="Content to write.")
@click.pass_context
def write_file_cmd(ctx, file_path, content):
    working_dir = ctx.obj["working_dir"]
    click.echo(write_file(working_dir, file_path, content))


@cli.command("run-python")
@click.argument("file_path")
@click.option("--arg", "args", multiple=True, help="Argument for the script.")
@click.pass_context
def run_python(ctx, file_path, args):
    working_dir = ctx.obj["working_dir"]
    click.echo(run_python_file(working_dir, file_path, list(args)))
