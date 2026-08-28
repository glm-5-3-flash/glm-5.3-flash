import requests
import json
import base64
from typing import List, Dict, Any, Generator

class GLM53FlashClient:
    """
    API Client wrapper for GLM-5.3-Flash (0x Alpha).
    Supports 1M token context, streaming responses, and multimodal input.
    """
    def __init__(self, api_key: str = "free-preview", base_url: str = "https://api.z.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = "glm-5.3-flash"

    def _encode_image(self, image_path: str) -> str:
        """Encodes a local image file to base64 string for vision capabilities."""
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    def build_multimodal_message(self, text: str, code_files: List[str] = None, image_paths: List[str] = None) -> Dict[str, Any]:
        """
        Formats user prompt with attached codebase files (for 1M context) 
        and visual screenshots/diagrams into OpenAI-compatible format.
        """
        content_payload = []

        # 1. Attach Codebase Context
        if code_files:
            code_context = "\n\n=== ATTACHED LOCAL CODEBASE FILES ===\n"
            for file_path in code_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code_context += f"\n--- File: {file_path} ---\n{f.read()}\n"
                except Exception as e:
                    code_context += f"\n--- File: {file_path} (Failed to load: {e}) ---\n"
            text = code_context + "\n=== USER QUERY ===\n" + text

        content_payload.append({"type": "text", "text": text})

        # 2. Attach Images (Vision-Assisted Dev)
        if image_paths:
            for img in image_paths:
                b64_data = self._encode_image(img)
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_data}"}
                })

        return {"role": "user", "content": content_payload}

    def generate_stream(self, messages: List[Dict[str, Any]], temperature: float = 0.2) -> Generator[str, None, None]:
        """
        Sends request to GLM-5.3-Flash endpoint and yields response tokens continuously.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": 131072 # High output limit for entire modules
        }

        endpoint = f"{self.base_url}/chat/completions"

        try:
            response = requests.post(endpoint, headers=headers, json=payload, stream=True, timeout=60)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json["choices"][0]["delta"].get("content", "")
                            yield delta
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[API Connection Error: {str(e)} - Running in offline fallback demo mode]\n"
            # Fallback mock response for standalone testing
            yield f"GLM-5.3-Flash (0x Alpha) processed your input with high-speed streaming capabilities."
