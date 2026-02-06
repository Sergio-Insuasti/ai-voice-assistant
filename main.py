
from VoiceAssistant import VoiceAssistant
def main():
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print("Fatal error:", e)


if __name__ == "__main__":
    main()