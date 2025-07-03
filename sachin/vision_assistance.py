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
import threading
import time
from pathlib import Path
import platform
import subprocess


import dwani
import os

dwani.api_key = os.getenv("DWANI_API_KEY")

dwani.api_base = os.getenv("DWANI_API_BASE_URL")


# Initialize OpenAI clients
server_url = os.getenv("API_SERVER")
vlm_server_url = os.getenv("API_SERVER_VLM")
tts_server_url = "https://dwani-whisper.hf.space/v1"

tool_client = OpenAI(base_url=server_url, api_key="EMPTY")
image_client = OpenAI(base_url=vlm_server_url, api_key="EMPTY")
tts_client = OpenAI(base_url=tts_server_url, api_key="cant-be-empty")

# Define the tools
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

# Shared variable to store the latest image description
latest_image_description = {"description": "", "timestamp": None}
description_lock = threading.Lock()

# Function to get the current time for a given timezone
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

# Function to capture and describe a webcam frame
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

        # Save the frame to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name
            cv2.imwrite(temp_path, frame)

        # Convert image to base64 for API
        with open(temp_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Clean up temporary file
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}", file=sys.stderr)

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

# Background thread to capture images every 10 seconds
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
        time.sleep(10)  # Wait for 10 seconds before next capture

# Function to record and transcribe audio
def record_and_transcribe():
    duration = 5  # seconds per chunk
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



        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(wav_io.getvalue())
            temp_file_path = temp_file.name
        result = dwani.ASR.transcribe(file_path=temp_file_path, language="english")
        import os
        os.unlink(temp_file_path)  # Clean up the temporary file
        print("ASR Response:", result)
        return result["text"]

    except Exception as e:
        print(f"Error during recording or transcription: {str(e)}")
        return None

# Function to generate and play speech
def generate_and_play_speech(text):
    try:

        response = dwani.Audio.speech(input=text, response_format="wav", language="english")
        

        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(response)

        # Play the audio based on the operating system
        system = platform.system()
        try:
            if system == "Windows":
                process = subprocess.run(["start", str(temp_path)], shell=True)
            elif system == "Darwin":  # macOS
                process = subprocess.run(["afplay", str(temp_path)])
            elif system == "Linux":
                process = subprocess.run(["aplay", str(temp_path)])
            else:
                print(f"Autoplay not supported on {system}. Open {temp_path} manually.")
                return
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}", file=sys.stderr)

    except Exception as e:
        print(f"Error generating speech: {str(e)}")

# Modified chat function with single-line output
def chat_with_qwen3():
    messages = []
    print("Voice chat active. Speak for 5s (Ctrl+C to stop).")
    # Start background image capture thread
    image_thread = threading.Thread(target=background_image_capture, daemon=True)
    image_thread.start()

    try:
        while True:
            # Record and transcribe audio input
            transcribed_text = record_and_transcribe()
            if not transcribed_text or transcribed_text.isspace():
                print("No valid input, waiting...")
                continue

            # Get the latest image description
            with description_lock:
                image_description = latest_image_description["description"]
                image_timestamp = latest_image_description["timestamp"]
                timestamp_str = (datetime.fromtimestamp(image_timestamp).strftime('%H:%M:%S')
                                 if image_timestamp else "No image")

            # Combine transcribed text with the latest image description
            prompt = f"User: {transcribed_text} | Image ({timestamp_str}): {image_description or 'No description'}"
            messages.append({"role": "user", "content": prompt})

            # Process the prompt with the chat model
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

                # Handle tool calls
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
                        else:
                            print(f"Unknown tool: {tool_call.function.name}")
                    # Continue processing with tool outputs
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
                    # No tool calls, print and play the response
                    print(f"Assistant: {response_message.content.strip()}")
                    generate_and_play_speech(response_message.content)
                    messages.append({"role": "assistant", "content": response_message.content})

            except Exception as e:
                print(f"Error processing response: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("Chat stopped. History saved to 'conversation_history.json'.")
        with open("conversation_history.json", "w") as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Fatal error: {str(e)}")

# Run the chat
if __name__ == "__main__":
    import sys
    chat_with_qwen3()