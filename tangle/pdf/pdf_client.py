
import base64
import os

from typing import Optional, Type
from pydantic import BaseModel, ValidationError
from perplexity import Perplexity

class PerplexityPDFClient:
    def __init__(self):
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("Missing PERPLEXITY_API_KEY in environment variables")
        self.client = Perplexity(api_key=api_key)

    def encode_pdf(self, pdf_path: str) -> str:
        """Encode a local PDF file into a base64 string."""
        with open(pdf_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    def generate_text(
        self,
        pdf_file: str,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ):
        encoded_pdf = self.encode_pdf(pdf_file)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "file_url",
                        "file_url": {
                            "url" : encoded_pdf
                        }
                    }
                ]
            }
        ]

        response_format = None
        if response_model:
            response_format = {
                "type": "json_schema",
                "json_schema": {"schema": response_model.model_json_schema()},
            }

        completion = self.client.chat.completions.create(
            model="sonar-pro",
            messages=messages,
            response_format=response_format,
        )

        raw_response = completion.choices[0].message.content

        if response_model:
            try:
                return response_model.model_validate_json(raw_response)
            except ValidationError as e:
                raise ValueError(f"Response parsing failed: {e}")

        return raw_response
