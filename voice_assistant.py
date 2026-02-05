import speech_recognition as sr, pyttsx3
from google import genai
from secrets import INSTRUCTIONS, GOOGLE_API
import re

def clean_response(text:str) -> str:
    # Remove bold / italics (**text**, *text*)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)

    # Remove inline code (`text`)
    text = re.sub(r'`(.*?)`', r'\1', text)

    # Remove headings (#)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    return text.strip()

client = genai.Client(GOOGLE_API)
r = sr.Recognizer()
tts = pyttsx3.init()

with sr.Microphone() as mic:
    print("Speak...")
    spoken = r.recognize_google(r.listen(mic))
    
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"""{INSTRUCTIONS}{spoken}
    """
)

reply = clean_response(resp.text)
print("Assistant :", reply)
tts.say(reply)
tts.runAndWait()