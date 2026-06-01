from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
	def __init__(self, code: str, message: str, status_code: int = 500, details: Any | None = None) -> None:
		super().__init__(message)
		self.code = code
		self.message = message
		self.status_code = status_code
		self.details = details

	def to_payload(self) -> dict[str, dict[str, Any | None]]:
		return {
			"error": {
				"code": self.code,
				"message": self.message,
				"details": self.details,
			}
		}


class ValidationAppError(AppError):
	def __init__(self, code: str, message: str, details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=400, details=details)


class UnauthorizedError(AppError):
	def __init__(self, code: str, message: str = "Authentication is required.", details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=401, details=details)


class ForbiddenError(AppError):
	def __init__(self, code: str, message: str = "You do not have permission to perform this action.", details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=403, details=details)


class ConflictError(AppError):
	def __init__(self, code: str, message: str, details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=409, details=details)


class PayloadTooLargeError(AppError):
	def __init__(self, code: str, message: str, details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=413, details=details)


class UnsupportedMediaTypeError(AppError):
	def __init__(self, code: str, message: str, details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=415, details=details)


class NotFoundError(AppError):
	def __init__(self, code: str, message: str, details: Any | None = None) -> None:
		super().__init__(code=code, message=message, status_code=404, details=details)


def build_server_error() -> dict[str, dict[str, Any | None]]:
	return {
		"error": {
			"code": "server_error",
			"message": "An unexpected error occurred.",
			"details": None,
		}
	}


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
	return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
	return JSONResponse(
		status_code=422,
		content={
			"error": {
				"code": "validation_error",
				"message": "Request validation failed.",
				"details": exc.errors(),
			}
		},
	)


async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
	return JSONResponse(status_code=500, content=build_server_error())