from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AuthSessionRecord:
    session_id: str
    organization_id: str
    user_id: str
    jti: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime


@dataclass(slots=True)
class AuthContext:
    token: str
    claims_jti: str
    session: AuthSessionRecord
    user: "UserRecord"