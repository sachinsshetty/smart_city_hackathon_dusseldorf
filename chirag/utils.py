import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64
import requests

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SD_API_URL = os.getenv("HUGGINGFACE_API_URL")

def analyze_image_with_gemini_api(image, improvement_type='smart_city', api_key=None):
    if api_key is None:
        api_key = GEMINI_API_KEY
    # Convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    # Compose prompt
    if improvement_type == 'smart_city':
        prompt = (
            "You are a smart city planner. Analyze the following street image and suggest improvements to make it more tech-friendly, sustainable, or environment-friendly. List specific suggestions, and if no changes are needed, say so."
        )
    else:
        prompt = (
            "You are an accessibility expert. Analyze the following street image and suggest improvements to make it more accessible for visually impaired and disabled people. List specific suggestions, and if no changes are needed, say so."
        )
    # Prepare API call (updated model)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        # Extract the model's reply
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def generate_finalized_image_with_sd(original_image, suggestions):
    # Convert image to base64
    buffered = io.BytesIO()
    original_image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    # Compose prompt for Stable Diffusion
    prompt = (
        "Modify this street scene as follows: "
        f"{suggestions}. The image should look realistic and show the suggested changes clearly."
    )
    # Call Hugging Face Space or Colab API with image-to-image
    payload = {
        "prompt": prompt,
        "init_image": img_b64,  # This key may vary by API!
        "strength": 0.7,
        "num_inference_steps": 30,
        "guidance_scale": 7.5
    }
    response = requests.post(SD_API_URL, json=payload)
    print("Stable Diffusion API status:", response.status_code)
    print("Stable Diffusion API response:", response.text)
    if response.status_code == 200:
        result = response.json()
        # Assume the API returns a URL or base64 image string
        if "image_url" in result:
            return result["image_url"]
        elif "image_base64" in result:
            return "data:image/png;base64," + result["image_base64"]
    return None 