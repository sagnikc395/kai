import os

from dotenv import load_dotenv
from google import genai
import click
import sys
from google.genai import types

DEBUG = True


def auth():
    load_dotenv()
    return os.environ.get("GEMINI_API_KEY")


@click.command()
@click.argument("prompt", required=False)
@click.option("--debug", is_flag=True, help="Print Debug Information (API KEY)")
def main(prompt: str | None, debug: bool):
    if prompt is None:
        raise click.UsageError(
            'Missing PROMPT argumen.\n\nUsage:\n  agent "your prompt here"'
        )

    api_key = auth()
    if api_key is None:
        raise click.ClickException("Please set GEMINI_API_KEY in your environment.")

    if debug:
        click.echo(f"[DEBUG] API Key: {api_key}")

    client = genai.Client(api_key=api_key)

    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]

    response = client.models.generate_content(
        model="gemini-3-flas-preview", contents=messages
    )

    if response is None or response.usage_metadata is None:
        raise click.ClickException("Response is malformed")

    click.echo(response.text)
    click.echo(f"Prompt tokens : {response.usage_metadata.prompt_token_count}")
    click.echo(f"Response tokens: {response.usage_metadata.candidates_token_count}")


if __name__ == "__main__":
    main()
