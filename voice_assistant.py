import asyncio
import speech_recognition as sr
import pyttsx3
import requests
from concurrent.futures import ThreadPoolExecutor
from utils.text_cleaner import clean_response

# =========================
# Configuration
# =========================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# =========================
# Global resources
# =========================

recognizer = sr.Recognizer()
tts = pyttsx3.init()

# CRITICAL: single worker only
executor = ThreadPoolExecutor(max_workers=1)

# =========================
# Blocking I/O functions
# =========================

def listen_blocking() -> str:
    """
    Capture audio from the microphone and perform speech recognition.
    This function is blocking and runs in the executor.
    """
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.2)
        audio = recognizer.listen(mic)
        return recognizer.recognize_google(audio)


def speak_blocking(text: str) -> None:
    """
    Perform text-to-speech playback.
    This runs synchronously and must not overlap with listening.
    """
    tts.say(text)
    tts.runAndWait()


def llm_blocking(prompt: str) -> str:
    """
    Call the local Ollama LLM synchronously.
    Exactly one call at a time is allowed.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    return clean_response(response.json()["response"])

# =========================
# Async wrappers
# =========================

async def listen() -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, listen_blocking)


async def ask_llm(prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, llm_blocking, prompt)

# =========================
# Main conversation loop
# =========================

async def conversation_loop():
    print("Your Assistant is now ready. Speak into the microphone.")

    while True:
        try:
            # 1. LISTEN
            spoken = await listen()
            print(f"You: {spoken}")

            # 2. EXIT COMMAND
            if spoken.lower() in {"exit", "quit", "leave"}:
                speak_blocking("Thank you Sergio! Have a great day!")
                break

            # 3. THINK (LLM)
            reply = await ask_llm(spoken)
            print(f"Assistant: {reply}")

            # 4. SPEAK
            speak_blocking(reply)

        except sr.UnknownValueError:
            speak_blocking(
                "I'm sorry, but I was not able to understand you. Please try again."
            )

        except Exception as e:
            print("Error:", e)
            speak_blocking(
                "Oh! Something went wrong on our end. Want to try that again?"
            )

# =========================
# Entry point
# =========================

if __name__ == "__main__":
    asyncio.run(conversation_loop())
