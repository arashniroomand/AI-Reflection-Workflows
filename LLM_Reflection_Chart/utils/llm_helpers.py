import os
import base64
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """Initialize OpenAI client configured for custom base URL host."""
    api_key = os.environ.get("OPENAI_API_KEY", "dummy_key")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.gapgpt.app/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def encode_image_to_base64(image_path: str) -> str:
    """Encode local image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_response(model_name: str, prompt: str) -> str:
    """Get text response from model using OpenAI-compatible endpoint."""
    client = get_openai_client()
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def image_openai_call(model_name: str, prompt: str, image_path: str) -> str:
    """Send image alongside text prompt using OpenAI multi-modal API payload format."""
    client = get_openai_client()
    base64_image = encode_image_to_base64(image_path)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                },
            ],
        }
    ]
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content