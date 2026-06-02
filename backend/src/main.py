from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.auth import router as auth_router
from .api.routes.audit import router as audit_router
from .api.routes.files import router as files_router
from .api.routes.floors import router as floors_router
from .api.routes.health import router as health_router
from .api.routes.users import router as users_router
from .core.config.settings import get_settings
from .infrastructure.mongo.auth_repository import AuthRepository
from .infrastructure.mongo.audit_repository import AuditRepository
from .infrastructure.mongo.file_repository import FileRepository
from .infrastructure.mongo.client import MongoDatabaseClient
from .services.audit_service import AuditService
from .services.auth_service import AuthService
from .services.file_service import FileService
from .services.user_service import UserService
from .utils.errors import AppError, app_error_handler, unexpected_error_handler, validation_error_handler

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.parsed_cors_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

mongo_client = MongoDatabaseClient(settings.mongodb_uri, settings.mongodb_database)
auth_repository = AuthRepository(mongo_client, settings)
audit_repository = AuditRepository(mongo_client)
audit_service = AuditService(audit_repository, auth_repository)
auth_service = AuthService(auth_repository, audit_service, settings)
file_repository = FileRepository(mongo_client)
file_service = FileService(file_repository, auth_repository, audit_service, settings)
user_service = UserService(auth_repository, audit_service, settings)

app.state.settings = settings
app.state.mongo_client = mongo_client
app.state.auth_repository = auth_repository
app.state.audit_repository = audit_repository
app.state.audit_service = audit_service
app.state.auth_service = auth_service
app.state.file_repository = file_repository
app.state.file_service = file_service
app.state.user_service = user_service

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(floors_router, prefix="/api")


@app.on_event("shutdown")
def close_mongo_client() -> None:
	mongo_client.close()
