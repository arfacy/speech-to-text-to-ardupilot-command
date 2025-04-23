import os
import sys
import pyaudio
import tkinter as tk
from tkinter import messagebox
import threading
from pynput import keyboard
from SpeechModelContext import SpeechModelContext
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import re
import unicodedata
import math
from dronekit import VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
from turkce_sayi import text_to_number


vehicle = connect("udp:127.0.0.1:14550", wait_ready=True)
print(f"Bağlandı: {vehicle.version}")

class CommandInterpreter:
    def normalize(self, raw_text: str) -> str:
        text = raw_text.lower().strip()  # Türkçe karakterleri KORU!
        text = re.sub(r"\s+", " ", text)  # gereksiz boşlukları sadeleştir
        print(f"[DEBUG normalize] raw: '{raw_text}' | normalized: '{text}'")

        if re.search(r"\b(kalk|havalan|uç|yukarı çık)\b", text):
            return "kalk"
        
        if re.search(r"\b(in|iniş|aşağı in|yere in)\b", text):
            return "in"

        if match := re.search(r"\bi̇leri\s*(\d+)\b", text):
            return f"ileri {match.group(1)}"
        
        if match := re.search(r"\bgeri\s*(\d+)\b", text):
            return f"geri {match.group(1)}"
        
        if match := re.search(r"\b(yukarı|çık)\s*(\d+)\b", text):
            return f"çık {match.group(2)}"

        if match := re.search(r"\b(alçal|aşağı)\s*(\d+)\b", text):
            return f"alçal {match.group(2)}"
        
        if match := re.search(r"\birtifa\s+(\d+)(\.|inci)?\s*metre\b", text):
            return f"irtifa {match.group(1)}"
        
        if match := re.search(r"\bsağa\s*(\d+)\b", text):
            return f"sağa {match.group(1)}"

        if match := re.search(r"\bsola\s*(\d+)\b", text):
            return f"sola {match.group(1)}"
        
        if match := re.search(r"\b(\d+)\s*derece\s+sağa\b", text):
            return f"derece sağa {match.group(1)}"

        if match := re.search(r"\b(\d+)\s*derece\s+sola\b", text):
            return f"derece sola {match.group(1)}"

        return "anlaşılamadı"




class CommandParser:
    def __init__(self, vehicle):
        self.vehicle = vehicle

    def arm_and_takeoff(self, target_altitude: float):
        self.vehicle.mode = VehicleMode("GUIDED")
        while not self.vehicle.is_armable:
            time.sleep(1)
        self.vehicle.armed = True
        while not self.vehicle.armed:
            time.sleep(1)
        self.vehicle.simple_takeoff(target_altitude)
        while True:
            if self.vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
                break
            time.sleep(1)

    def land(self):
        self.vehicle.mode = VehicleMode("LAND")

    def goto_forward_relative(self, meters: float, groundspeed=2):
        loc = self.vehicle.location.global_relative_frame
        heading = math.radians(self.vehicle.heading)

        dNorth = meters * math.cos(heading)
        dEast = meters * math.sin(heading)

        dLat = dNorth / 111320
        dLon = dEast / (111320 * math.cos(math.radians(loc.lat)))

        target = LocationGlobalRelative(loc.lat + dLat, loc.lon + dLon, loc.alt)
        self.vehicle.simple_goto(target, groundspeed=groundspeed)

        
    def goto_backward_relative(self, meters: float, groundspeed=2):
        loc = self.vehicle.location.global_relative_frame
        heading = math.radians(self.vehicle.heading)

        # geri = heading + 180 derece
        heading += math.pi

        dNorth = meters * math.cos(heading)
        dEast = meters * math.sin(heading)

        dLat = dNorth / 111320
        dLon = dEast / (111320 * math.cos(math.radians(loc.lat)))

        target = LocationGlobalRelative(loc.lat + dLat, loc.lon + dLon, loc.alt)
        self.vehicle.simple_goto(target, groundspeed=groundspeed)


    def goto_left_relative(self, meters: float, groundspeed=2):
        loc = self.vehicle.location.global_relative_frame
        heading = math.radians(self.vehicle.heading)

        angle = heading - math.pi / 2
        dNorth = meters * math.cos(angle)
        dEast = meters * math.sin(angle)
        dLat = dNorth / 111320
        dLon = dEast / (111320 * math.cos(math.radians(loc.lat)))
        target = LocationGlobalRelative(loc.lat + dLat, loc.lon + dLon, loc.alt)
        self.vehicle.simple_goto(target, groundspeed=groundspeed)

    def goto_right_relative(self, meters: float, groundspeed=2):
        loc = self.vehicle.location.global_relative_frame
        heading = math.radians(self.vehicle.heading)

        angle = heading + math.pi / 2
        dNorth = meters * math.cos(angle)
        dEast = meters * math.sin(angle)
        dLat = dNorth / 111320
        dLon = dEast / (111320 * math.cos(math.radians(loc.lat)))
        target = LocationGlobalRelative(loc.lat + dLat, loc.lon + dLon, loc.alt)
        self.vehicle.simple_goto(target, groundspeed=groundspeed)

    def rotate_yaw(self, angle: float, direction: str, yaw_speed: float = 60):
        direction_flag = 1 if direction == "derece sağa" else -1

        full_turns = int(angle // 360)
        remainder = angle % 360

        for _ in range(full_turns):
            msg = self.vehicle.message_factory.command_long_encode(
                0, 0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                360,
                yaw_speed,
                direction_flag,
                1,  # relative
                0, 0, 0
            )
            self.vehicle.send_mavlink(msg)
            self.vehicle.flush()
            time.sleep(360 / yaw_speed)

        if remainder > 0:
            msg = self.vehicle.message_factory.command_long_encode(
                0, 0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                remainder,
                yaw_speed,
                direction_flag,
                1,  # relative
                0, 0, 0
            )
            self.vehicle.send_mavlink(msg)
            self.vehicle.flush()
            time.sleep(remainder / yaw_speed)




    def goto_altitude(self, altitude: float):
        loc = self.vehicle.location.global_relative_frame
        target = LocationGlobalRelative(loc.lat, loc.lon, altitude)
        self.vehicle.simple_goto(target)

    def get_current_altitude(self):
        return self.vehicle.location.global_relative_frame.alt

    def parse_and_execute(self, command: str):
        if command == "kalk":
            self.arm_and_takeoff(10)
        elif command == "in":
            self.land()
        elif command.startswith("ileri"):
            meters = float(command.split()[1])
            self.goto_forward_relative(meters)

        elif command.startswith("geri"):
            meters = float(command.split()[1])
            self.goto_backward_relative(meters)

        elif command.startswith("çık"):
            alt = float(command.split()[1])
            self.goto_altitude(self.get_current_altitude() + alt)
        elif command.startswith("alçal"):
            alt = float(command.split()[1])
            self.goto_altitude(self.get_current_altitude() - alt)
        elif command.startswith("sağa"):
            meters = float(command.split()[1])
            self.goto_right_relative(meters)
        elif command.startswith("sola"):
            meters = float(command.split()[1])
            self.goto_left_relative(meters)
        elif command.startswith("derece sağa"):
            angle = float(command.split()[2])
            self.rotate_yaw(angle, "derece sağa")
        elif command.startswith("derece sola"):
            angle = float(command.split()[2])
            self.rotate_yaw(angle, "derece sola")
        elif command.startswith("irtifa"):
            target_alt = float(command.split()[1])
            self.goto_altitude(target_alt)
        else:
            print("Tanımsız komut")


parser = CommandParser(vehicle)

class SpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sesli Komut - Vosk")
        self.root.geometry("500x300")

        self.model_context = SpeechModelContext()
        self.command_interpreter = CommandInterpreter()

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

        self.listen_button = tk.Label(
            root,
            text="🎤 Dinleme Durum: PASİF",
            bg="lightcoral",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=10,
            pady=5
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
            self.text_display.insert("1.0", f"Hata: {str(e)}\n")   

    def process_audio(self):
        audio_data = b''.join(self.audio_buffer)
        text = self.model_context.transcribe(audio_data)
        text = text_to_number(text)

        if text:
            self.text_display.insert("1.0", f"Tanınan metin: {text}\n")
            if "dur" in text:
                self.text_display.insert("1.0", "🛑 Program durduruluyor...\n")
                self.cleanup_and_exit()
                return

            normalized = self.command_interpreter.normalize(text)
            self.text_display.insert("1.0", f"🤖 Yorumlanan komut: {normalized}\n")
            parser.parse_and_execute(normalized)
        else:
            self.text_display.insert("1.0", "Metin tanınamadı.\n")

    def cleanup_and_exit(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.root.quit()
        self.root.destroy()
        vehicle.close()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechApp(root)
    root.mainloop()


"""

cd ~/Desktop/Speech-To-Text/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -v ArduCopter -f quad --console --map


cd ~/Desktop/Speech-To-Text/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -v ArduCopter -f quad --map --console

"""