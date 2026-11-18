import ollama

from config import MODEL


def stream_chat(messages):
    stream = ollama.chat(
        model=MODEL,
        messages=messages,
        stream=True
    )

    for chunk in stream:
        content = chunk["message"]["content"]

        if content:
            yield content


def ask(messages):
    full_response = ""

    print("\nMistral > ", end="", flush=True)

    try:
        for content in stream_chat(messages):
            print(
                content,
                end="",
                flush=True
            )

            full_response += content

    except Exception:
        print("\nErreur : impossible de contacter Ollama.")
        print("Vérifie que `ollama serve` est lancé.")

        return None

    print()

    return full_response