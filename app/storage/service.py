"""Secure file storage service handling uploads, deduplication hashing, and diagram crops."""

import hashlib
import io
import os
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from PIL import Image
from app.core.config import settings
from app.storage.validators import sanitize_filename, validate_file_content_and_type


class StorageService:
    def __init__(self, upload_dir: Optional[Path] = None, crops_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.crops_dir = crops_dir or settings.CROPS_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.crops_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(
        self,
        file_obj: BinaryIO,
        filename: str,
        user_id: str,
    ) -> Tuple[str, str, int, str]:
        """
        Stream upload to disk, calculate SHA-256 hash, validate magic bytes.
        Returns: (relative_file_path, file_sha256_hash, file_size_bytes, detected_mime)
        """
        clean_name = sanitize_filename(filename)
        ext = clean_name.split(".")[-1] if "." in clean_name else "bin"
        unique_name = f"{user_id}_{uuid.uuid4().hex[:12]}.{ext}"
        destination_path = self.upload_dir / unique_name

        hasher = hashlib.sha256()
        total_bytes = 0
        header_bytes = b""

        # Read in chunks (64 KB)
        chunk_size = 64 * 1024
        with open(destination_path, "wb") as dest:
            while chunk := file_obj.read(chunk_size):
                if total_bytes == 0:
                    header_bytes = chunk[:64]
                total_bytes += len(chunk)
                hasher.update(chunk)
                dest.write(chunk)

        try:
            # Validate magic bytes and size
            detected_mime = validate_file_content_and_type(header_bytes, clean_name, total_bytes)
        except Exception:
            # Clean up corrupted/rejected upload file from disk
            if destination_path.exists():
                destination_path.unlink()
            raise

        file_hash = hasher.hexdigest()
        return str(destination_path), file_hash, total_bytes, detected_mime

    def save_crop_image(self, image: Image.Image, filename_prefix: str = "diagram") -> str:
        """
        Save cropped question diagram or figure to crops storage directory.
        Returns: relative file path.
        """
        crop_name = f"{filename_prefix}_{uuid.uuid4().hex[:10]}.png"
        crop_path = self.crops_dir / crop_name
        image.save(crop_path, format="PNG", optimize=True)
        return str(crop_path)

    def delete_file(self, file_path: str) -> bool:
        """Securely delete file from disk."""
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False


storage_service = StorageService()
