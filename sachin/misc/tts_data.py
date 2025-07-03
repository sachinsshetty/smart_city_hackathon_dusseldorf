from pathlib import Path
import platform
import subprocess


import dwani
import os

dwani.api_key = os.getenv("DWANI_API_KEY")

dwani.api_base = os.getenv("DWANI_API_BASE_URL")

response = dwani.Audio.speech(input="What is your name?", response_format="wav", language="english")
print("Audio Speech: Output saved to output.wav")


# Save the audio to a file
output_file = Path("output.wav")
with output_file.open("wb") as f:
    f.write(response)

# Autoplay the audio based on the operating system
def play_audio(file_path):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["start", str(file_path)], shell=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["afplay", str(file_path)])
        elif system == "Linux":
            subprocess.run(["aplay", str(file_path)])
        else:
            print(f"Autoplay not supported on {system}. Please open {file_path} manually.")
    except Exception as e:
        print(f"Error playing audio: {e}")

play_audio(output_file)