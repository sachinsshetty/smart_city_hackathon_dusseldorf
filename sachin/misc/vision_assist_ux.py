from fasthtml.common import *
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
import threading
import time
from pathlib import Path
import platform
import subprocess
from openai import OpenAI
import glob

# Set up FastHTML app
app = FastHTML()

# Directory for images (for timestamps, not display)
IMAGE_DIR = "images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Path to conversation history
HISTORY_FILE = "conversation_history.json"

# Initialize OpenAI clients
server_url = os.getenv("API_SERVER", "http://localhost:8000/v1")  # Default for local testing
vlm_server_url = os.getenv("API_SERVER_VLM", "http://localhost:8001/v1")  # Default for local testing
tts_server_url = "https://dwani-whisper.hf.space/v1"

tool_client = OpenAI(base_url=server_url, api_key="EMPTY")
image_client = OpenAI(base_url=vlm_server_url, api_key="EMPTY")
tts_client = OpenAI(base_url=tts_server_url, api_key="cant-be-empty")  # Replace with valid key

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local time for a specified timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The IANA timezone name (e.g., Europe/Berlin)"
                    }
                },
                "required": ["timezone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_webcam_image",
            "description": "Capture a single frame from the default webcam and return a description. Description should be 2 lines max",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Shared variable for latest image description
latest_image_description = {"description": "", "timestamp": None}
description_lock = threading.Lock()

# Function to get current time
def get_current_time(timezone):
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        formatted_time = current_time.strftime("%I:%M:%S %p %Z, %A, %B %d, %Y")
        return {"timezone": timezone, "current_time": formatted_time}
    except pytz.exceptions.UnknownTimeZoneError:
        return {"error": f"Invalid timezone: {timezone}"}
    except Exception as e:
        return {"error": f"Failed to fetch time for {timezone}: {str(e)}"}

# Function to capture and describe webcam image
def capture_webcam_image():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Failed to open webcam"}

        ret, frame = cap.read()
        if not ret:
            cap.release()
            return {"error": "Failed to capture image from webcam"}

        cap.release()

        # Save image to IMAGE_DIR with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(IMAGE_DIR, f"webcam_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)

        # Convert image to base64 for API
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Send image to Gemma3-4B-IT for description
        try:
            response = image_client.chat.completions.create(
                model="Gemma3-4B-IT",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.0,
                max_tokens=32768
            )
            description = response.choices[0].message.content
            return {"description": description, "timestamp": time.time()}
        except Exception as e:
            return {"error": f"Failed to get image description: {str(e)}"}

    except Exception as e:
        return {"error": f"Error capturing webcam image: {str(e)}"}

# Background thread for periodic image capture
def background_image_capture():
    global latest_image_description
    while True:
        image_data = capture_webcam_image()
        with description_lock:
            if "description" in image_data:
                latest_image_description = {
                    "description": image_data["description"],
                    "timestamp": image_data["timestamp"]
                }
        time.sleep(10)  # Capture every 10 seconds

# Function to record and transcribe audio
def record_and_transcribe():
    duration = 5  # seconds
    sample_rate = 16000
    channels = 1

    try:
        print("Recording for 5 seconds... Speak now.")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
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
                print(f"Transcribed: {transcription}")
                return transcription
            else:
                print("Transcription empty, try again.")
                return None
        else:
            print(f"Transcription error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error during recording or transcription: {str(e)}")
        return None

# Function to generate and play speech
def generate_and_play_speech(text):
    try:
        res = tts_client.audio.speech.create(
            model="speaches-ai/Kokoro-82M-v1.0-ONNX",
            voice="af_heart",
            input=text,
            response_format="wav",
            speed=1,
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(res.response.read())

        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["start", str(temp_path)], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["afplay", str(temp_path)])
            elif system == "Linux":
                subprocess.run(["aplay", str(temp_path)])
            else:
                print(f"Autoplay not supported on {system}. Open {temp_path} manually.")
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}")

    except Exception as e:
        print(f"Error generating speech: {str(e)}")

# Function to handle voice chat
def chat_with_qwen3():
    messages = []
    print("Voice chat active. Speak for 5s (Ctrl+C to stop).")
    try:
        while True:
            transcribed_text = record_and_transcribe()
            if not transcribed_text or transcribed_text.isspace():
                print("No valid input, waiting...")
                continue

            with description_lock:
                image_description = latest_image_description["description"]
                image_timestamp = latest_image_description["timestamp"]
                timestamp_str = (datetime.fromtimestamp(image_timestamp).strftime('%H:%M:%S')
                                 if image_timestamp else "No image")

            prompt = f"User: {transcribed_text} | Image ({timestamp_str}): {image_description or 'No description'}"
            messages.append({"role": "user", "content": prompt})

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
                            messages.append({
                                "role": "tool",
                                "content": json.dumps(time_data),
                                "tool_call_id": tool_call.id
                            })
                        elif tool_call.function.name == "capture_webcam_image":
                            image_data = capture_webcam_image()
                            messages.append({
                                "role": "tool",
                                "content": json.dumps(image_data),
                                "tool_call_id": tool_call.id
                            })
                    response = tool_client.chat.completions.create(
                        model="Qwen3-32B",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.0,
                        max_tokens=32768
                    )
                    response_message = response.choices[0].message
                    print(f"Assistant: {response_message.content.strip()}")
                    generate_and_play_speech(response_message.content)
                    messages.append({"role": "assistant", "content": response_message.content})
                else:
                    print(f"Assistant: {response_message.content.strip()}")
                    generate_and_play_speech(response_message.content)
                    messages.append({"role": "assistant", "content": response_message.content})

            except Exception as e:
                print(f"Error processing response: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("Chat stopped. History saved to 'conversation_history.json'.")
        with open(HISTORY_FILE, "w") as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Fatal error: {str(e)}")

# Function to get latest image description and timestamp
def get_latest_image_info():
    image_files = glob.glob(f"{IMAGE_DIR}/*.jpg")
    timestamp = None
    if image_files:
        latest_image = max(image_files, key=os.path.getmtime)
        timestamp = datetime.fromtimestamp(os.path.getmtime(latest_image)).strftime('%H:%M:%S')
    
    description = "No description available"
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        for message in reversed(history):
            if message.get("role") == "tool":
                content = json.loads(message["content"])
                if content.get("description"):
                    description = content["description"]
                    break
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return {
        "description": description,
        "timestamp": timestamp or "N/A"
    }

# Function to get latest conversation
def get_latest_conversation():
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        latest_input = "No input available"
        latest_output = "No output available"
        for message in reversed(history):
            if message.get("role") == "user" and latest_input == "No input available":
                latest_input = message.get("content", "No input available")
            elif message.get("role") == "assistant" and latest_output == "No output available":
                latest_output = message.get("content", "No output available")
            if latest_input != "No input available" and latest_output != "No output available":
                break
        return {"input": latest_input, "output": latest_output}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"input": "No input available", "output": "No output available"}

# FastHTML route for dashboard
@app.get("/")
def home():
    image_info = get_latest_image_info()
    conversation = get_latest_conversation()
    
    content = [
        H1("Webcam and Voice Chat Dashboard"),
        H2("Latest Webcam Image Description"),
        Div(
            P(f"Timestamp: {image_info['timestamp']}"),
            P(f"Description: {image_info['description']}")
        ),
        H2("Latest Conversation"),
        Div(
            P(Strong("Input: "), conversation["input"]),
            P(Strong("Output: "), conversation["output"])
        ),
        Button("Refresh", hx_get="/", hx_swap="outerHTML", hx_target="body")
    ]
    
    return Title("Webcam Chat Dashboard"), Main(*content, style="padding: 20px;")

# Start voice chat and web server
def main():
    # Start background image capture
    image_thread = threading.Thread(target=background_image_capture, daemon=True)
    image_thread.start()
    
    # Start voice chat in a separate thread
    chat_thread = threading.Thread(target=chat_with_qwen3, daemon=True)
    chat_thread.start()
    
    # Start FastHTML server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()