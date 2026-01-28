import os

from dotenv import load_dotenv
from google import genai
import sys
from google.genai import types


def auth():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    return api_key


def main():
    api_key = auth()
    if api_key is None:
        print("ERR: Please setup an api key before proceeding")
        sys.exit(1)
    print(f"API key: ${api_key}")

    if len(sys.argv) < 2:
        print("ERR: Need a prompt!")
        sys.exit(1)
    prompt = sys.argv[1]
    client = genai.Client(api_key=api_key)

    

    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=prompt.strip()
    )

    print(response.text)
    if response is None or response.usage_metadata is None:
        print("ERR: Response is malformed")
        sys.exit(1)
    print(f"Prompt tokens : {response.usage_metadata.prompt_token_count}")  # type: ignore
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")  # type: ignore


if __name__ == "__main__":
    main()
