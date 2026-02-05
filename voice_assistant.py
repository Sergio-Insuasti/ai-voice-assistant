import asyncio
import speech_recognition as sr
import pyttsx3
from google import genai
from secrets import INSTRUCTIONS, GOOGLE_API
from utils.text_cleaner import clean_response
from concurrent.futures import ThreadPoolExecutor

client = genai.Client(GOOGLE_API)
recogniser = sr.Recognizer()
tts = pyttsx3.init()
executor = ThreadPoolExecutor()

def listen_blocking():
    pass

def speak_blocking():
    pass

def llm_blocking():
    pass


async def listen():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, listen_blocking)

async def ask_llm(prompt: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, llm_blocking, prompt)

async def speak(text: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, speak_blocking, text)

async def conversation_loop():
    print("Your Assistant is now ready. Speak into the microphone")
    
    while True:
        try:
            spoken = await listen()
            
            if spoken.lower() in {"exit", "quit", "leave"}:
                tts.say("Thank you Sergio! Have a great day!")
                break
                
            reply = await ask_llm(spoken)
            
            asyncio.create_task(speak(reply))
        except sr.UnknownValueError:
            tts.say("I'm sorry, but I was not able to understand you. Please try again")
        except Exception as e:
            continue



if __name__ == "__main__":
    asyncio.run(conversation_loop())