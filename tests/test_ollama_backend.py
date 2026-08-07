from kai.api.ollama_backend import _to_ollama_messages


def test_message_conversion_for_ollama():
    messages = [
        {"role": "user", "content": "list the files"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "glob",
                        "arguments": '{"pattern": "*.txt"}',
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_abc", "content": "alpha.txt"},
    ]

    converted = _to_ollama_messages(messages)

    assert [m["role"] for m in converted] == ["user", "assistant", "tool"]
    # Ollama wants an argument object, not a JSON string.
    assert converted[1]["tool_calls"][0]["function"]["arguments"] == {
        "pattern": "*.txt"
    }
    # `content: None` would be rejected by the chat template.
    assert converted[1]["content"] == ""
    # The tool result is labelled by name since Ollama has no tool_call_id.
    assert converted[2]["tool_name"] == "glob"


def test_malformed_tool_arguments_become_empty_object():
    messages = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_bad",
                    "function": {"name": "read", "arguments": "{not json"},
                }
            ],
        }
    ]

    converted = _to_ollama_messages(messages)

    assert converted[0]["tool_calls"][0]["function"]["arguments"] == {}
