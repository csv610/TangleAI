import base64
import os
from pathlib import Path
from typing import Optional
from perplexity import Perplexity


class PerplexityVisionClient:
    """
    Simple client for Perplexity API with vision capabilities.

    API Limitations:
    - Max file size: 50MB per image
    - Supported formats: PNG, JPEG, WEBP, GIF
    - Images cannot be used with regex in the same request
    - sonar-deep-research does not support image input
    - Supported models: sonar-pro, sonar
    """

    # Supported image formats
    SUPPORTED_FORMATS = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    # Models that support images
    SUPPORTED_MODELS = ["sonar-pro", "sonar"]

    # API limits
    MAX_IMAGE_SIZE_MB = 50

    def __init__(self, model: str = "sonar-pro"):
        """
        Initialize client.

        Args:
            model: Model name (default: sonar-pro)

        Raises:
            ValueError: If model unsupported or API key missing
        """
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model}' does not support images. "
                f"Supported: {', '.join(self.SUPPORTED_MODELS)}"
            )

        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")

        self.model = model
        self.client = Perplexity(api_key=api_key)

    def generate_text(self, image_path: str, prompt: str = "Please describe this image.") -> str:
        """
        Send image to Perplexity and get text response.

        Args:
            image_path: Path to image file
            prompt: Prompt text (default: "Please describe this image.")

        Returns:
            Response text from API

        Raises:
            FileNotFoundError: If image file not found
            ValueError: If file invalid (unsupported format, too large)
            Exception: If API call fails
        """
        path = Path(image_path)

        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Validate format
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            supported = ", ".join(self.SUPPORTED_FORMATS.keys())
            raise ValueError(f"Unsupported format '{suffix}'. Supported: {supported}")

        # Validate file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_IMAGE_SIZE_MB:
            raise ValueError(
                f"File too large ({file_size_mb:.2f}MB). "
                f"Max: {self.MAX_IMAGE_SIZE_MB}MB"
            )

        # Encode image
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        # Build message
        mime_type = self.SUPPORTED_FORMATS[suffix]
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{encoded}"}
                    }
                ]
            }
        ]

        # Call API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False
        )

        # Extract response
        if not response or not response.choices:
            raise ValueError("Invalid API response")

        return response.choices[0].message.content


def main():
    """CLI entry point."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Analyze images with Perplexity API",
        epilog="Example: python image_client.py photo.jpg -p 'What is this?'"
    )
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("-p", "--prompt", help="Custom prompt", default="Please describe this image.")
    parser.add_argument("-m", "--model", help="Model name", default="sonar-pro")

    args = parser.parse_args()

    try:
        client = PerplexityVisionClient(model=args.model)
        result = client.generate_text(args.image, prompt=args.prompt)
        print(result)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
