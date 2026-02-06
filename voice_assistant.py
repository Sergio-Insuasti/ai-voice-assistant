import requests
import json
from secrets import OLLAMA_URL, OLLAMA_MODEL

def ask_ollama_stream(prompt: str) -> str:
    """
    Synchronous streaming call to Ollama.
    Tokens are yielded incrementally to reduce perceived latency.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 96,
            "temperature": 0.6
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=120
    )
    response.raise_for_status()

    full_response = []

    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line.decode("utf-8"))

        if "response" in data:
            token = data["response"]
            print(token, end="", flush=True)
            full_response.append(token)

        if data.get("done", False):
            break

    print()
    return "".join(full_response).strip()

def main():
    print("Ollama assistant ready (streaming).")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Assistant: Goodbye!")
            break

        try:
            print("Assistant: ", end="", flush=True)
            ask_ollama_stream(user_input)
            print()

        except Exception as e:
            print("\nError:", e)
            print("Assistant: Something went wrong. Try again.\n")

if __name__ == "__main__":
    main()
