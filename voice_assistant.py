import sys
import requests
from typing import Optional
import speech_recognition as sr
import pyttsx3
import time

from model_secrets import OLLAMA_URL, OLLAMA_MODEL, INSTRUCTIONS
from utils.text_cleaner import clean_response

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 300

        self.base_url = OLLAMA_URL.rstrip("/")
        self.model = OLLAMA_MODEL
        self.history = [{
            "role": "system",
            "content": INSTRUCTIONS.strip()
        }]

        self.tts_rate = 250
        self.tts_volume = 1.0

        print("Voice Assistant initialized")
        print(f"Model: {self.model}")
        print(f"Ollama: {self.base_url}")

        self.check_ollama()

    def check_ollama(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            print("Connected to Ollama\n")
        except Exception as e:
            print("Ollama not reachable")
            print(e)
            sys.exit(1)

    # -------------------------
    # Speak - FIX: Reinitialize TTS each time
    # -------------------------

    def speak(self, text: str):
        text = text.strip()
        if not text:
            return

        print(f"Assistant: {text}")

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.tts_rate)
            engine.setProperty("volume", self.tts_volume)
            
            engine.say(text)
            engine.runAndWait()
            
            engine.stop()
            del engine
            
        except Exception as e:
            print(f"TTS error: {e}")

        # Small delay to let audio complete
        time.sleep(0.2)

    def listen(self) -> Optional[str]:
        print("\nListening...")

        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=8
                )
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                return text

            except sr.WaitTimeoutError:
                print("No speech detected")
                self.speak("What's on your mind? Make sure to tell me!")
            except sr.UnknownValueError:
                print("Could not understand")
                self.speak("I'm sorry, I didn't quite get that.")
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                self.speak("I'm sorry, I didn't quite get that.")

        return None

    def get_ai_response(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": False
        }

        try:
            print("Thinking...")
            r = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            r.raise_for_status()

            data = r.json()
            content = data.get("message", {}).get("content", "")

            if isinstance(content, list):
                raw = " ".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict)
                )
            else:
                raw = content

            cleaned = clean_response(raw)
            self.history.append({"role": "assistant", "content": cleaned})
            return cleaned

        except Exception as e:
            print("LLM error:", e)
            return "Sorry, something went wrong."

    def run(self):
        self.speak("Hello! Anything I can help you with today?")

        while True:
            user_text = self.listen()
            if user_text is None:
                continue

            if user_text.lower() in {"exit", "quit", "stop", "goodbye"}:
                self.speak("Goodbye.")
                break

            reply = self.get_ai_response(user_text)
            self.speak(reply)


def main():
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        assistant.speak("Shutting down.")
    except Exception as e:
        print("Fatal error:", e)


if __name__ == "__main__":
    main()