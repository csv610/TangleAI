"""Image processing utilities for vision analysis."""

import base64
import logging
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io

from config import IMAGE_MIME_TYPE

logger = logging.getLogger(__name__)

# API constraints
MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_TOTAL_IMAGE_PAYLOAD_MB = 50
MAX_TOTAL_IMAGE_PAYLOAD_BYTES = MAX_TOTAL_IMAGE_PAYLOAD_MB * 1024 * 1024
MIN_IMAGE_DIMENSION = 32  # Minimum 32x32 pixels

class ImageUtils:
    """Handles image encoding and validation."""

    @staticmethod
    def encode_to_base64(image_path: str) -> str:
        """
        Convert an image file to base64 encoding.

        Args:
            image_path: Path to the image file

        Returns:
            Base64 encoded image URL in data URI format

        Raises:
            FileNotFoundError: If the image file doesn't exist
            ValueError: If file is not a valid image or exceeds size limit
        """
        path = Path(image_path)

        if not path.exists():
            logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if not ImageUtils.is_valid_image(path):
            logger.error(f"Invalid image file: {image_path}")
            raise ValueError(f"File is not a valid image: {image_path}. Supported formats: PNG, JPEG, WEBP, GIF")

        if not ImageUtils.is_valid_dimensions(path):
            try:
                with Image.open(path) as img:
                    width, height = img.size
                logger.error(f"Image dimensions too small: {image_path} ({width}x{height})")
            except:
                pass
            raise ValueError(f"Image must be at least {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION} pixels: {image_path}")

        if not ImageUtils.is_valid_size(path):
            file_size_mb = path.stat().st_size / (1024 * 1024)
            logger.error(f"Image file too large: {image_path} ({file_size_mb:.2f}MB)")
            raise ValueError(f"Image file exceeds {MAX_IMAGE_SIZE_MB}MB limit: {image_path} ({file_size_mb:.2f}MB)")

        try:
            with open(path, "rb") as file:
                file_data = file.read()
                encoded_file = base64.b64encode(file_data).decode("utf-8")
                base64_url = f"data:{IMAGE_MIME_TYPE};base64,{encoded_file}"
            return base64_url
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise

    @staticmethod
    def is_valid_image(path: Path) -> bool:
        """
        Check if a file is a valid image based on extension.

        Args:
            path: Path object to the file

        Returns:
            True if file has a valid image extension, False otherwise
        """
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        return path.suffix.lower() in valid_extensions

    @staticmethod
    def is_valid_size(path: Path) -> bool:
        """
        Check if image file size is within the 50MB limit.

        Args:
            path: Path object to the file

        Returns:
            True if file size is <= 50MB, False otherwise
        """
        return path.stat().st_size <= MAX_IMAGE_SIZE_BYTES

    @staticmethod
    def is_valid_dimensions(path: Path) -> bool:
        """
        Check if image dimensions meet minimum requirement (32x32).

        Args:
            path: Path object to the file

        Returns:
            True if image is at least 32x32 pixels, False otherwise
        """
        try:
            with Image.open(path) as img:
                width, height = img.size
                return width >= MIN_IMAGE_DIMENSION and height >= MIN_IMAGE_DIMENSION
        except Exception as e:
            logger.error(f"Error reading image dimensions: {e}")
            return False

    @staticmethod
    def _estimate_base64_size(data: bytes) -> int:
        """
        Estimate the base64 encoded size of binary data.

        Args:
            data: Binary data

        Returns:
            Estimated size in bytes after base64 encoding
        """
        # Base64 encoding increases size by ~33%
        return int(len(data) * 4 / 3) + 50  # +50 for data URI prefix overhead

    @staticmethod
    def _resize_image_to_quality(image_path: str, quality: int = 85, scale_factor: float = 1.0) -> bytes:
        """
        Resize and compress an image to specified quality and dimensions.

        Args:
            image_path: Path to the image file
            quality: JPEG quality (1-100), default 85
            scale_factor: Scale factor for dimensions (0.0-1.0), default 1.0 (no scaling)

        Returns:
            Compressed image data as bytes

        Raises:
            ValueError: If scaled dimensions would be below minimum
        """
        try:
            with Image.open(image_path) as img:
                # Calculate scaled dimensions
                if scale_factor < 1.0:
                    new_width = max(MIN_IMAGE_DIMENSION, int(img.width * scale_factor))
                    new_height = max(MIN_IMAGE_DIMENSION, int(img.height * scale_factor))
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert RGBA to RGB if necessary (for JPEG compatibility)
                if img.mode in ("RGBA", "LA", "P"):
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = rgb_img

                # Save with compression
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=quality, optimize=True)
                return output.getvalue()
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            raise

    @staticmethod
    def resize_images_to_fit(image_paths: List[str]) -> List[str]:
        """
        Automatically resize images so total payload doesn't exceed limit.

        Resizes images proportionally if their combined base64 size exceeds the limit.
        Returns paths to resized temporary images or original paths if no resizing needed.

        Args:
            image_paths: List of image file paths

        Returns:
            List of image paths (original or resized temporary files)

        Raises:
            ValueError: If images cannot be resized to fit within limit
        """
        if not image_paths:
            return image_paths

        # Calculate total size
        total_size = 0
        image_data = []
        for path in image_paths:
            p = Path(path)
            with open(p, "rb") as f:
                data = f.read()
                image_data.append(data)
                total_size += ImageUtils._estimate_base64_size(data)

        # If within limit, return original paths
        if total_size <= MAX_TOTAL_IMAGE_PAYLOAD_BYTES:
            logger.info(f"Total image payload {total_size / 1024 / 1024:.2f}MB is within {MAX_TOTAL_IMAGE_PAYLOAD_MB}MB limit")
            return image_paths

        # Need to resize - start with quality 85 and reduce if needed
        logger.warning(f"Total image payload {total_size / 1024 / 1024:.2f}MB exceeds limit. Auto-resizing...")

        quality = 85
        scale_factor = 1.0

        while quality > 10 or scale_factor < 1.0:
            resized_data = []
            total_resized_size = 0

            for i, path in enumerate(image_paths):
                try:
                    compressed = ImageUtils._resize_image_to_quality(path, quality, scale_factor)
                    resized_data.append(compressed)
                    total_resized_size += ImageUtils._estimate_base64_size(compressed)
                except Exception as e:
                    logger.error(f"Failed to resize {path} at quality {quality}, scale {scale_factor:.2f}: {e}")
                    raise

            if total_resized_size <= MAX_TOTAL_IMAGE_PAYLOAD_BYTES:
                # Write resized images to temporary files
                temp_paths = []
                for i, data in enumerate(resized_data):
                    temp_path = Path(image_paths[i]).parent / f".{Path(image_paths[i]).stem}_resized_{quality}_{int(scale_factor*100)}.jpg"
                    with open(temp_path, "wb") as f:
                        f.write(data)
                    temp_paths.append(str(temp_path))
                    logger.info(f"Resized {Path(image_paths[i]).name} to {temp_path.stat().st_size / 1024 / 1024:.2f}MB (quality {quality}, scale {scale_factor:.2f})")

                return temp_paths

            # Reduce quality first, then scale if quality hits minimum
            if quality > 10:
                quality -= 5
            else:
                scale_factor -= 0.1

        # If we get here, even at quality 10 and heavily scaled it's too large
        raise ValueError(
            f"Cannot resize images to fit within {MAX_TOTAL_IMAGE_PAYLOAD_MB}MB limit. "
            f"Total size at minimum settings: {total_resized_size / 1024 / 1024:.2f}MB"
        )
