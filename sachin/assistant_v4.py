from openai import OpenAI
import json
from datetime import datetime
import pytz
import cv2
import os
import tempfile
import base64
import io
import sounddevice as sd
import wavio
import httpx
import pyttsx3

# Initialize TTS engine globally
try:
    tts_engine = pyttsx3.init('espeak')
    tts_engine.setProperty('rate', 150)
except Exception as e:
    print(f"TTS init error: {str(e)}")
    tts_engine = None

def speak_text(text):
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {str(e)}")

# Initialize OpenAI clients
server_url = os.getenv("API_SERVER")
vlm_server_url = os.getenv("API_SERVER_VLM")
tool_client = OpenAI(base_url=server_url, api_key="EMPTY")
image_client = OpenAI(base_url=vlm_server_url, api_key="EMPTY")

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current local time for a timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "IANA timezone (e.g., Europe/Berlin)"}
                },
                "required": ["timezone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_webcam_image",
            "description": "Capture webcam frame and describe it",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

def get_current_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz).strftime("%I:%M:%S %p %Z, %A, %B %d, %Y")
        return {"timezone": timezone, "current_time": current_time}
    except pytz.exceptions.UnknownTimeZoneError:
        return {"error": f"Invalid timezone: {timezone}"}
    except Exception as e:
        return {"error": f"Failed to fetch time: {str(e)}"}

def capture_webcam_image():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Failed to open webcam"}
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return {"error": "Failed to capture image"}
        cap.release()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, frame)
        with open(temp_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"Warning: Could not delete temp file: {str(e)}")
        try:
            response = image_client.chat.completions.create(
                model="Gemma3-4B-IT",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image in one sentence for a blind user, including key objects and their positions."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                temperature=0.0,
                max_tokens=32768
            )
            description = response.choices[0].message.content
            return {"image_path": temp_path, "description": description}
        except Exception as e:
            return {"error": f"Failed to get image description: {str(e)}"}
    except Exception as e:
        return {"error": f"Error capturing image: {str(e)}"}

def record_and_transcribe():
    duration = 5
    sample_rate = 16000
    channels = 1
    try:
        speak_text("Recording starting now")
        print("\nRecording for 5 seconds...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
        speak_text("Recording complete")
        print("Recording complete. Transcribing...")
        wav_io = io.BytesIO()
        wavio.write(wav_io, audio_data, sample_rate, sampwidth=2)
        wav_io.seek(0)
        files = {
            'file': ('microphone.wav', wav_io, 'audio/wav'),
            'model': (None, 'Systran/faster-whisper-small')
        }
        response = httpx.post('https://dwani-whisper.hf.space/v1/audio/transcriptions', files=files)
        if response.status_code == 200:
            transcription = response.text.strip()
            if transcription:
                print(f"Transcription: {transcription}")
                speak_text(f"You said: {transcription}")
                return transcription
            else:
                print("Transcription empty.")
                speak_text("Transcription empty, try again")
                return None
        else:
            print(f"Transcription error: {response.status_code}")
            speak_text("Transcription failed, try again")
            return None
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        speak_text("Error in recording, try again")
        return None

def chat_with_qwen3():
    messages = []
    print("Starting voice chat. Speak (5s). Press Ctrl+C to stop.")
    speak_text("Starting voice chat. Speak prompt. Press Control C to stop.")
    try:
        while True:
            transcribed_text = record_and_transcribe()
            if not transcribed_text or transcribed_text.isspace():
                print("Empty transcription, waiting...")
                continue
            prompt = transcribed_text
            messages.append({"role": "user", "content": prompt})
            print(f"\nUser: {prompt}")
            try:
                response = tool_client.chat.completions.create(
                    model="Qwen3-32B",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.0,
                    max_tokens=32768
                )
                response_message = response.choices[0].message
                if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        if tool_call.function.name == "get_current_time":
                            args = json.loads(tool_call.function.arguments)
                            timezone = args.get("timezone", "Europe/Berlin")
                            time_data = get_current_time(timezone)
                            messages.append({"role": "tool", "content": json.dumps(time_data), "tool_call_id": tool_call.id})
                        elif tool_call.function.name == "capture_webcam_image":
                            image_data = capture_webcam_image()
                            messages.append({"role": "tool", "content": json.dumps(image_data), "tool_call_id": tool_call.id})
                        else:
                            print(f"Unknown tool: {tool_call.function.name}")
                    response = tool_client.chat.completions.create(
                        model="Qwen3-32B",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.0,
                        max_tokens=32768
                    )
                    response_message = response.choices[0].message
                    print(f"Qwen3: {response_message.content}\n")
                    speak_text(response_message.content)
                    messages.append({"role": "assistant", "content": response_message.content})
                else:
                    print(f"Qwen3: {response_message.content}\n")
                    speak_text(response_message.content)
                    messages.append({"role": "assistant", "content": response_message.content})
            except Exception as e:
                print(f"Chat error: {str(e)}")
                speak_text("Chat error, try again")
                continue
    except KeyboardInterrupt:
        print("\nChat stopped.")
        speak_text("Chat stopped")
        with open("conversation_history.json", "w") as f:
            json.dump(messages, f, indent=2)
        print("History saved to 'conversation_history.json'.")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        speak_text("Fatal error, session stopped")
    finally:
        if tts_engine:
            tts_engine.stop()
            del tts_engine

if __name__ == "__main__":
    chat_with_qwen3()