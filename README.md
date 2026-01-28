# kai

building an small agent from scratch using tool calling.

## Setup

- this model currently uses the free flash model from Google Gemini, feel free to swap with other models
- steps to create and load your own API key:
  - generate your API key from google genai studio
  - copy the api key info
  - copy the `.env.local` file into `.env`
  - paste the api key in GEMINI_API_KEY field

## running

- setup uv
- run it as
`uv run kai.py`
