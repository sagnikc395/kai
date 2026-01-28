import os

from dotenv import load_dotenv
from google import genai


def auth():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    return api_key


def main():
    api_key = auth()
    print(f"API key: ${api_key}")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="i want to organize the worlds's knowledge into a few bytes, what should i convey ?",
    )

    print(response.text)
    if response is None or response.usage_metadata is None:
        return
    print(f"Prompt tokens : {response.usage_metadata.prompt_token_count}")  # type: ignore
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")  # type: ignore


if __name__ == "__main__":
    main()
