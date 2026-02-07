import subprocess
import tempfile
import os
import winsound

from model_secrets import PIPER_EXE, PIPER_MODEL

def speak(text: str):
    if not text: return
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        wav_path = f.name
        
    subprocess.run(
        [
            PIPER_EXE,
            "--model", PIPER_MODEL,
            "--length_scale", "0.8",
            "--output_file", wav_path
        ],
        input=text,
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print(text)
    
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)

    os.remove(wav_path)