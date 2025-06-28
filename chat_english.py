import dwani
import os

# Set API key and base URL
dwani.api_key = os.getenv("DWANI_API_KEY")
dwani.api_base = os.getenv("DWANI_API_BASE_URL")


response = dwani.Chat.direct(prompt="Hello!")
print("Chat Response:  ",response)


response = dwani.Vision.caption_direct(file_path="image.png",
            query="Describe this image",model="gemma3"
            )
print("Vision Response:  ",response)
    