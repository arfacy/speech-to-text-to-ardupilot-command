import os
import json
import vosk


class SpeechModelContext:
    def __init__(self, model_path: str = "vosk-model-small-tr-0.3"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model bulunamadı: {model_path}")
        
        self.model = vosk.Model(model_path)
        self.rec = vosk.KaldiRecognizer(self.model, 16000)

    def transcribe(self, audio_data: bytes) -> str:
        if self.rec.AcceptWaveform(audio_data):
            result = json.loads(self.rec.Result())
        else:
            result = json.loads(self.rec.FinalResult())
        return result.get("text", "").strip().lower()
