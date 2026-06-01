from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
	return datetime.now(timezone.utc)


def ensure_utc(value: datetime | None) -> datetime | None:
	if value is None:
		return None
	if value.tzinfo is None:
		return value.replace(tzinfo=timezone.utc)
	return value.astimezone(timezone.utc)


def to_iso(value: datetime | None) -> str | None:
	if value is None:
		return None
	normalized = ensure_utc(value)
	return normalized.isoformat().replace("+00:00", "Z") if normalized is not None else None


def now_utc_iso() -> str:
	return to_iso(now_utc()) or ""
