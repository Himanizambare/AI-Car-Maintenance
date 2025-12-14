# agents/voice_agent_ui.py
import pyttsx3
import threading

class VoiceAgentServer:
    def __init__(self, rate: int = 150, speak_enabled: bool = True):
        self.speak_enabled = speak_enabled
        if speak_enabled:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", rate)
        else:
            self.engine = None

    def speak_async(self, text: str):
        """Run TTS in separate thread so Streamlit UI doesn't freeze for long scripts."""
        if not self.speak_enabled:
            print("[VOICE DISABLED] " + text)
            return

        def runner():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print("TTS failed:", e)

        t = threading.Thread(target=runner, daemon=True)
        t.start()

    def speak(self, text: str):
        """Synchronous speak (small text)"""
        if self.speak_enabled:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print("[VOICE DISABLED] " + text)
