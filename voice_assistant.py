import requests
from secrets import OLLAMA_MODEL, OLLAMA_URL
from utils.text_cleaner import clean_response

def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )
    
    response.raise_for_status()
    
    return clean_response(response.json()["response"].strip())

def main():
    print("Ollama assistant ready. Type your message.")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Assistant: Goodbye!")
            break

        try:
            reply = ask_ollama(user_input)
            print(f"Assistant: {reply}\n")

        except Exception as e:
            print("Error:", e)
            print("Assistant: Something went wrong. Try again.\n")

if __name__ == "__main__":
    main()
    