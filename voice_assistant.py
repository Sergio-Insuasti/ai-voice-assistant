import speech_recognition as sr, pyttsx3
from google import genai
from secrets import INSTRUCTIONS, GOOGLE_API
from utils.text_cleaner import clean_response

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