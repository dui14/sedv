from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json

from ...utils.errors import UnauthorizedError


@dataclass(slots=True)
class AccessTokenClaims:
    sub: str
    org: str
    jti: str
    email: str
    full_name: str
    role: str
    status: str
    iat: int
    exp: int
    typ: str = "access"


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def encode_access_token(claims: AccessTokenClaims, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_segment = _base64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_segment = _base64url_encode(json.dumps(asdict(claims), separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"


def decode_access_token(token: str, secret: str) -> AccessTokenClaims:
    parts = token.split(".")
    if len(parts) != 3:
        raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        provided_signature = _base64url_decode(signature_segment)
    except Exception as exc:  # pragma: no cover - defensive
        raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.") from exc
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.")
    try:
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
        claims = AccessTokenClaims(**payload)
    except Exception as exc:  # pragma: no cover - defensive
        raise UnauthorizedError(code="unauthorized", message="The access token is invalid or expired.") from exc
    return claims