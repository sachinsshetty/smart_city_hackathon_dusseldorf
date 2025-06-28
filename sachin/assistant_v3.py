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

# Initialize OpenAI clients
server_url = os.getenv("API_SERVER")
vlm_server_url = os.getenv("API_SERVER_VLM")

tool_client = OpenAI(base_url=server_url, api_key="EMPTY")
image_client = OpenAI(base_url=vlm_server_url, api_key="EMPTY")

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
            "description": "Capture a single frame from the default webcam and return a description",
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
            # Suppress all output, including errors, to avoid clutter
        time.sleep(10)  # Wait for 10 seconds before next capture

# Function to record and transcribe audio
def record_and_transcribe():
    duration = 5  # seconds per chunk
    sample_rate = 16000
    channels = 1

    try:
        print("\nRecording for 5 seconds... (Speak now)")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
        print("Recording complete. Sending audio for transcription...")

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
                return transcription
            else:
                print("Transcription empty, please try again.")
                return None
        else:
            print(f"Transcription error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Error during recording or transcription: {str(e)}")
        return None

# Modified chat function
def chat_with_qwen3():
    messages = []
    print("Starting voice-activated continuous chat session with background image processing.")
    print("Speak your prompt (5 seconds per recording). Press Ctrl+C to stop.")

    # Start background image capture thread
    image_thread = threading.Thread(target=background_image_capture, daemon=True)
    image_thread.start()

    try:
        while True:
            # Record and transcribe audio input
            transcribed_text = record_and_transcribe()
            if not transcribed_text or transcribed_text.isspace():
                print("No valid transcription (empty or whitespace), waiting for next input...")
                continue

            # Get the latest image description
            with description_lock:
                image_description = latest_image_description["description"]
                image_timestamp = latest_image_description["timestamp"]
                timestamp_str = (datetime.fromtimestamp(image_timestamp).strftime('%H:%M:%S')
                                 if image_timestamp else "No image yet")

            # Combine transcribed text with the latest image description
            prompt = f"User voice input: {transcribed_text}\nLatest image description (captured at {timestamp_str}): {image_description or 'No image description available'}"
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
                            print(f"Unknown tool called: {tool_call.function.name}")
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
                    print(f"{response_message.content}\n")
                    messages.append({"role": "assistant", "content": response_message.content})
                else:
                    # No tool calls, print and add the response
                    print(f"{response_message.content}\n")
                    messages.append({"role": "assistant", "content": response_message.content})

            except Exception as e:
                print(f"Error processing chat response: {str(e)}")
                continue

    except KeyboardInterrupt:
        print("\nChat session stopped by user.")
        with open("conversation_history.json", "w") as f:
            json.dump(messages, f, indent=2)
        print("Conversation history saved to 'conversation_history.json'.")
    except Exception as e:
        print(f"Fatal error occurred: {str(e)}")

# Run the chat
if __name__ == "__main__":
    import sys
    chat_with_qwen3()