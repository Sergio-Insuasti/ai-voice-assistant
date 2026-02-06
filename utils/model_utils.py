import sys
import time
import requests
import threading

from model_secrets import INSTRUCTIONS, OLLAMA_MODEL, OLLAMA_URL

def check_connection(url: str = OLLAMA_URL):
    try:
        r = requests.get(f"{url}/api/tags", timeout=5)
        r.raise_for_status()
        print("Connected to Ollama")
    except Exception as e:
        print("Ollama not reachable")
        print(e)
        sys.exit(1)

def warmup_model(model:str = OLLAMA_MODEL, url:str = OLLAMA_URL):
        """
        Warm up the LLM by loading it into memory to reduce first-query latency.
        Uses /api/chat so the actual chat path is primed.
        """
        warmup_complete = threading.Event()
        
        def do_warmup():
            warmup_payload = {
                "model": model,
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
                    f"{url}/api/chat",
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
            line = f"Loading model into memory... [{bar}] {percent}%"
            print(
                f'\r{line:<100}',
                end='',
                flush=True
            )
            time.sleep(0.05)
        bar = '█' * bar_length
        final_line = f"Loading model into memory... [{bar}] 100%"
        print(f"\r{final_line:<100}", flush=True)
        print()
        
        warmup_thread.join(timeout=1)
        print("Model loaded!\n")