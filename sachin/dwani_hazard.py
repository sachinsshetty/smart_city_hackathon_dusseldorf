from openai import OpenAI
import json
from datetime import datetime
import pytz
import cv2
import os
import tempfile
import base64

# Global variable to track if the user clicked to send the image
send_image = False

# Mouse callback function to detect click
def mouse_callback(event, x, y, flags, param):
    global send_image
    if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse click
        send_image = True

# Initialize OpenAI clients
# For tool calls (Qwen3-32B)
import os

# Set API key and base URL
server_url = os.getenv("API_SERVER")
vlm_server_url = os.getenv("API_SERVER_VLM")

# Initialize the OpenAI client for llama.cpp's server
#client = OpenAI(base_url="http://localhost:9100/v1", api_key="EMPTY")


tool_client = OpenAI(base_url=server_url, api_key="EMPTY")
# For image description (Gemma3-4B-IT)
image_client = OpenAI(base_url=vlm_server_url, api_key="EMPTY")


#tool_client = OpenAI(base_url="http://localhost:9100/v1", api_key="EMPTY")
# For image description (Gemma3-4B-IT)
#image_client = OpenAI(base_url="http://localhost:9000/v1", api_key="EMPTY")

# Define the tools for getting the current time and capturing webcam image
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
            "description": "Capture a single frame from the default webcam, display it, and return a description on user click",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Function to get the current time for a given timezone using pytz
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

# Function to capture, display, and describe a webcam frame
def capture_webcam_image():
    global send_image
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Failed to open webcam"}

        ret, frame = cap.read()
        if not ret:
            cap.release()
            return {"error": "Failed to capture image from webcam"}

        # Display the captured frame
        cv2.namedWindow("Webcam Frame")
        cv2.setMouseCallback("Webcam Frame", mouse_callback)
        send_image = False  # Reset click flag

        # Show the frame until clicked or 'q' is pressed
        while True:
            cv2.imshow("Webcam Frame", frame)
            key = cv2.waitKey(1) & 0xFF
            if send_image or key == ord('q'):
                break

        cv2.destroyAllWindows()
        cap.release()

        if not send_image:
            return {"error": "Image not sent (user closed window without clicking)"}

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
            print(f"Warning: Could not delete temporary file {temp_path}: {str(e)}")

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
            return {"image_path": temp_path, "description": description}
        except Exception as e:
            return {"error": f"Failed to get image description: {str(e)}"}

    except Exception as e:
        return {"error": f"Error capturing webcam image: {str(e)}"}

import json

def chat_with_qwen3():
    user_prompts = [
        "What do you see?",
        "Do you see a hazard ?",
        "Is there a Yellow jacket in the picture?",
        "how should i move from here to the exit?"
        "What is the time in Bonn?",
    ]
    messages = []

    try:
        for prompt in user_prompts:
            # Add user message
            messages.append({"role": "user", "content": prompt})

            while True:
                response = tool_client.chat.completions.create(
                    model="Qwen3-32B",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.0,
                    max_tokens=32768
                )
                response_message = response.choices[0].message

                # If there are tool calls, handle them
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
                    # Continue the loop to let the model use the tool outputs
                else:
                    # No tool calls, print and add the response
                    print(f"Qwen3: {response_message.content}\n")
                    messages.append({"role": "assistant", "content": response_message.content})
                    break

    except Exception as e:
        print(f"Error occurred: {str(e)}")

# Run the chat
if __name__ == "__main__":
    chat_with_qwen3()