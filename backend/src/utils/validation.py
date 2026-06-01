from __future__ import annotations

import re

from .errors import ValidationAppError


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_string(value: str) -> str:
    return value.strip()


def normalize_email(value: str) -> str:
    email = normalize_string(value).lower()
    if not email or not EMAIL_PATTERN.match(email):
        raise ValidationAppError(code="invalid_payload", message="A valid email address is required.")
    return email


def validate_registration_password(value: str, minimum_length: int) -> str:
    password = normalize_string(value)
    if len(password) < minimum_length:
        raise ValidationAppError(
            code="invalid_payload",
            message=f"Password must be at least {minimum_length} characters long.",
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValidationAppError(
            code="invalid_payload",
            message="Password must contain at least one letter and one number.",
        )
    return password


def validate_login_password(value: str) -> str:
    password = normalize_string(value)
    if not password:
        raise ValidationAppError(code="invalid_payload", message="Password is required.")
    return password


def validate_full_name(value: str) -> str:
    full_name = normalize_string(value)
    if not full_name:
        raise ValidationAppError(code="invalid_payload", message="Full name is required.")
    if len(full_name) > 120:
        raise ValidationAppError(code="invalid_payload", message="Full name must be 120 characters or less.")
    return full_name


def validate_reason(value: str | None) -> str | None:
    if value is None:
        return None
    reason = normalize_string(value)
    return reason or None


def validate_search_term(value: str | None) -> str | None:
    if value is None:
        return None
    term = normalize_string(value)
    return term or None


def validate_file_name(value: str | None) -> str:
    file_name = normalize_string(value or "")
    if not file_name:
        raise ValidationAppError(code="invalid_upload", message="A file name is required.")
    if len(file_name) > 255:
        raise ValidationAppError(code="invalid_upload", message="File name must be 255 characters or less.")
    return file_name


def validate_upload_bytes(content: bytes, max_size_bytes: int) -> bytes:
    if not content:
        raise ValidationAppError(code="invalid_upload", message="A non-empty file is required.")
    if len(content) > max_size_bytes:
        from .errors import PayloadTooLargeError

        raise PayloadTooLargeError(code="file_too_large", message="The uploaded file exceeds the configured limit.")
    return content


def validate_upload_mime_type(value: str | None, allowed_types: list[str]) -> str:
    mime_type = normalize_string(value or "")
    if not mime_type:
        from .errors import UnsupportedMediaTypeError

        raise UnsupportedMediaTypeError(code="unsupported_media_type", message="A supported file type is required.")
    if mime_type not in allowed_types:
        from .errors import UnsupportedMediaTypeError

        raise UnsupportedMediaTypeError(code="unsupported_media_type", message="The uploaded file type is not supported.")
    return mime_type