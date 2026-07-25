"""
Input validation utilities — file size, MIME types, text sanitization.
"""
import re
from app.config import settings


ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/pdf",
    "application/vnd.ms-excel",
}

ALLOWED_EXTENSIONS = {".csv", ".pdf", ".txt"}


def validate_file_size(size_bytes: int) -> bool:
    """Check file size against MAX_UPLOAD_SIZE_MB."""
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    return size_bytes <= max_bytes


def validate_mime_type(content_type: str) -> bool:
    """Check if the file MIME type is allowed."""
    return content_type.lower() in ALLOWED_MIME_TYPES


def sanitize_text(text: str, max_length: int = 50000) -> str:
    """
    Sanitize user-supplied text:
    - Strip control characters (except newlines and tabs)
    - Cap total length
    - Normalize whitespace
    """
    if not text:
        return ""
    # Strip control characters except \n, \t, \r
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Cap length
    text = text[:max_length]
    return text.strip()


def validate_file_extension(filename: str) -> bool:
    """Check if the file extension is allowed."""
    if not filename:
        return False
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS
