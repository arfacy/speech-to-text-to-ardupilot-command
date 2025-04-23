# import os
# import pyaudio
# import vosk
# import json

# model_path = "vosk-model-small-tr-0.3"
# if not os.path.exists(model_path):
#     print(f"Model bulunamadı: {model_path}")
#     exit(1)

# model = vosk.Model(model_path)

# p = pyaudio.PyAudio()
# stream = p.open(format=pyaudio.paInt16,
#                 channels=1,
#                 rate=16000,
#                 input=True,
#                 frames_per_buffer=16384)

# print("Mikrofon dinleniyor... Konuşmaya başlayın. ('dur' kelimesini söyleyerek çıkabilirsiniz)")

# rec = vosk.KaldiRecognizer(model, 16000)

# while True:
#     data = stream.read(8192, exception_on_overflow=False)

#     if rec.AcceptWaveform(data):
#         result = json.loads(rec.Result())
#         text = result.get('text', '')

#         if text:
#             print(f"Tanınan metin: {text}")
#             if "dur" in text.lower():
#                 print("Program durduruluyor...")
#                 break
#         else:
#             print("Metin tanınamadı.")
#     else:
#         partial_result = json.loads(rec.PartialResult())
#         partial_text = partial_result.get('partial', '')
#         if partial_text:
#             print(f"Geçici metin: {partial_text}", end='\r')

# stream.stop_stream()
# stream.close()
# p.terminate()


"""import os
import pyaudio
import vosk
import json
import sys
from pynput import keyboard

model_path = "vosk-model-small-tr-0.3"
if not os.path.exists(model_path):
    print(f"Model bulunamadı: {model_path}")
    sys.exit(1)

model = vosk.Model(model_path)
rec = vosk.KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)

is_listening = False
audio_buffer = []
should_exit = False  # çıkış işareti

def on_press(key):
    global is_listening, audio_buffer
    if key == keyboard.Key.enter and not is_listening:
        is_listening = True
        audio_buffer = []
        print("Dinleme başladı...")

def on_release(key):
    global is_listening, should_exit
    if key == keyboard.Key.enter and is_listening:
        is_listening = False
        audio_data = b''.join(audio_buffer)
        if rec.AcceptWaveform(audio_data):
            result = json.loads(rec.Result())
            text = result.get('text', '')
        else:
            result = json.loads(rec.FinalResult())
            text = result.get('text', '')

        if text:
            print(f"Tanınan metin: {text}")
            if text.strip().lower() == "dur":
                print("Program durduruluyor...")
                should_exit = True
        else:
            print("Metin tanınamadı.")

def stop_program():
    stream.stop_stream()
    stream.close()
    p.terminate()
    listener.stop()
    print("Program tamamen kapatılıyor...")
    sys.exit(0)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Enter tuşuna basılı tutarak konuşun. 'dur' diyerek çıkabilirsiniz.")

try:
    while True:
        if should_exit:
            stop_program()
        if is_listening:
            data = stream.read(2048, exception_on_overflow=False)
            audio_buffer.append(data)
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
    stop_program()

    """

"""import os
import pyaudio
import sys
import numpy as np
from pynput import keyboard
from SpeechModelContext import SpeechModelContext


def is_significant_audio(audio_data: bytes, threshold=600):
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    amplitude = np.abs(audio_np).mean()
    return amplitude > threshold


model_context = SpeechModelContext()

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)

is_listening = False
audio_buffer = []
should_exit = False

def on_press(key):
    global is_listening, audio_buffer
    if key == keyboard.Key.enter and not is_listening:
        is_listening = True
        audio_buffer = []
        print("Dinleme başladı...")

def on_release(key):
    global is_listening, should_exit
    if key == keyboard.Key.enter and is_listening:
        is_listening = False
        audio_data = b''.join(audio_buffer)
        text = model_context.transcribe(audio_data)
        
        if text:
            print(f"Tanınan metin: {text}")
            if text == "dur":
                print("Program durduruluyor...")
                should_exit = True
        else:
            print("Metin tanınamadı.")

def stop_program():
    stream.stop_stream()
    stream.close()
    p.terminate()
    listener.stop()
    print("Program tamamen kapatılıyor...")
    sys.exit(0)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("Enter tuşuna basılı tutarak konuşun. 'dur' diyerek çıkabilirsiniz.")

try:
    while True:
        if should_exit:
            stop_program()
        if is_listening:
            data = stream.read(2048, exception_on_overflow=False)
            if is_significant_audio(data):
                audio_buffer.append(data)
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
    stop_program()
"""

import os
import sys
import pyaudio
import tkinter as tk
from tkinter import messagebox
import threading
from pynput import keyboard
from SpeechModelContext import SpeechModelContext

class SpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sesli Komut - Vosk")
        self.root.geometry("500x300")
        
        self.model_context = SpeechModelContext()
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=16000,
                                  input=True,
                                  frames_per_buffer=4096)
        
        self.audio_buffer = []
        self.is_listening = False
        self.listen_thread = None
        
        self.text_display = tk.Text(root, height=10, width=60)
        self.text_display.pack(pady=20)
        
        self.listen_button = tk.Label(root, text="🎤 Dinleme Durum: PASİF", bg="lightcoral", fg="white", font=("Segoe UI", 12, "bold"), padx=10, pady=5
)
        self.listen_button.pack()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()

    def on_key_press(self, key):
        if key == keyboard.Key.enter and not self.is_listening:
            self.is_listening = True
            self.audio_buffer = []
            self.listen_button.config(text="🎙️ Dinleniyor...", fg="white", bg="lightgreen")
            self.text_display.insert("1.0", "🎙️ Dinleme başladı...\n")
            self.listen_thread = threading.Thread(target=self.listen)
            self.listen_thread.start()

    def on_key_release(self, key):
        if key == keyboard.Key.enter and self.is_listening:
            self.is_listening = False
            self.listen_button.config(text="🎤 Dinleme Durum: PASİF", fg="white", bg="lightcoral")
            if self.listen_thread is not None:
                self.listen_thread.join()
            self.process_audio()

    def listen(self):
        try:
            while self.is_listening:
                data = self.stream.read(2048, exception_on_overflow=False)
                self.audio_buffer.append(data)
        except Exception as e:
            self.text_display.insert(tk.END, f"Hata: {str(e)}\n")

    def process_audio(self):
        audio_data = b''.join(self.audio_buffer)
        text = self.model_context.transcribe(audio_data)
        if text:
            self.text_display.insert("1.0", f"Tanınan metin: {text}\n")
            if "dur" in text.lower():
                self.text_display.insert("1.0", "🛑 Program durduruluyor...\n")
                self.cleanup_and_exit()
        else:
            self.text_display.insert("1.0", "Metin tanınamadı.\n")
    
    def cleanup_and_exit(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechApp(root)
    root.mainloop()

