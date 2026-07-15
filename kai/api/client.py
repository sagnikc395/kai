from groq import Groq


def create_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)
