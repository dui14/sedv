from __future__ import annotations

from fastapi import Request

from ...services.file_service import FileService


def get_file_service(request: Request) -> FileService:
	return request.app.state.file_service