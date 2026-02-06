import sys
import requests
from typing import Optional
import speech_recognition as sr
import pyttsx3
import time
import threading

from model_secrets import OLLAMA_URL, OLLAMA_MODEL, INSTRUCTIONS
from utils.text_cleaner import clean_response

class VoiceAssistant:
    def __init__(self):
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 300

        # Model setup
        self.base_url = OLLAMA_URL.rstrip("/")
        self.model = OLLAMA_MODEL
        self.history = [{
            "role": "system",
            "content": INSTRUCTIONS.strip()
        }]

        # TTS settings
        self.tts_rate = 300
        self.tts_volume = 1.0

        print("Voice Assistant initialized")
        print(f"Model: {self.model}")

        self.check_ollama()
        
        # Warm up the model with loading bar
        self.warmup_model()

    def check_ollama(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            r.raise_for_status()
            print("Connected to Ollama")
        except Exception as e:
            print("Ollama not reachable")
            print(e)
            sys.exit(1)

    def warmup_model(self):
        """
        Warm up the LLM by loading it into memory to reduce first-query latency.
        Uses /api/chat so the actual chat path is primed.
        """
        warmup_complete = threading.Event()
        
        def do_warmup():
            warmup_payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": INSTRUCTIONS.strip()},
                    {"role": "user", "content": "Hello"}
                ],
                "stream": False,
                "options": {
                    "num_predict": 1
                }
            }
            
            try:
                requests.post(
                    f"{self.base_url}/api/chat",
                    json=warmup_payload,
                    timeout=30
                )
            except Exception:
                pass
            
            warmup_complete.set()
        
        warmup_thread = threading.Thread(target=do_warmup)
        warmup_thread.start()
        
        bar_length = 40
        start_time = time.time()
        max_duration = 15.0
        
        while not warmup_complete.is_set():
            elapsed = time.time() - start_time
            
            if elapsed < max_duration:
                progress = min(elapsed / max_duration, 0.99)
            else:
                progress = 0.99
            
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            percent = int(progress * 100)
            print(
                f'\rLoading model into memory... [{bar}] {percent}%\n',
                end='',
                flush=True
            )
            time.sleep(0.05)
        print()
        
        warmup_thread.join(timeout=1)
        print("Model loaded!\n")
        

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

        time.sleep(0.2)

    def listen(self) -> Optional[str]:
        print("\nListening... (speak now)")

        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Ready - speak now!")
                
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )
                
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                return text

            except sr.WaitTimeoutError:
                print("No speech detected (timeout)")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error in listen: {e}")
                return None

    def get_ai_response_streaming(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True
        }

        try:
            print("Thinking...")
            
            r = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
                stream=True
            )
            r.raise_for_status()

            full_response = ""
            sentence_buffer = ""
            
            for line in r.iter_lines():
                if not line:
                    continue
                
                try:
                    data = line.decode('utf-8')
                    if data.startswith('data: '):
                        data = data[6:]
                    
                    import json
                    chunk = json.loads(data)
                    
                    if chunk.get("done"):
                        break
                    
                    content = chunk.get("message", {}).get("content", "")
                    if not content:
                        continue
                    
                    full_response += content
                    sentence_buffer += content
                    
                    if any(sentence_buffer.rstrip().endswith(p) for p in ['.', '!', '?', ':', ';']):
                        sentence = clean_response(sentence_buffer.strip())
                        if sentence:
                            self.speak(sentence)
                        sentence_buffer = ""
                
                except json.JSONDecodeError:
                    continue
            
            if sentence_buffer.strip():
                sentence = clean_response(sentence_buffer.strip())
                if sentence:
                    self.speak(sentence)
            
            cleaned = clean_response(full_response)
            self.history.append({"role": "assistant", "content": cleaned})
            return cleaned

        except Exception as e:
            print("LLM error:", e)
            error_msg = "Sorry, something went wrong."
            self.speak(error_msg)
            return error_msg

    def run(self):
        self.speak("Hello! Anything I can help you with today?")
        time.sleep(0.5)

        consecutive_failures = 0
        
        while True:
            user_text = self.listen()
            
            if user_text is None:
                consecutive_failures += 1
                if consecutive_failures == 2:
                    self.speak("I'm ready when you are. Just speak your question.")
                elif consecutive_failures >= 5:
                    self.speak("Still here if you need me.")
                    consecutive_failures = 0
                continue
            
            consecutive_failures = 0

            if user_text.lower() in {"exit", "quit", "stop", "goodbye", "bye"}:
                self.speak("Goodbye.")
                break

            self.get_ai_response_streaming(user_text)
