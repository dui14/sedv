from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from ...api.dependencies.auth import get_current_auth_context
from ...api.dependencies.files import get_file_service
from ...schemas.files import (
	FileAdminUpdateRequest,
	FileApproveRequest,
	FileDeleteResponse,
	FileItemResponse,
	FileListResponse,
	FileRejectRequest,
	PublishRequestListResponse,
	PublishRequestResponse,
	RequestPublishRequest,
)
from ...services.file_service import FileDownloadResult, FileService

router = APIRouter(prefix="/files", tags=["files"])


def _request_metadata(request: Request) -> tuple[str | None, str | None]:
	client_host = request.client.host if request.client else None
	user_agent = request.headers.get("user-agent")
	return client_host, user_agent


@router.get("", response_model=FileListResponse)
def list_files(
	request: Request,
	search: str | None = Query(default=None),
	vault_type: str | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileListResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.list_files(
		current_context,
		search=search,
		vault_type=vault_type,
		page=page,
		page_size=page_size,
		ip_address=ip_address,
		user_agent=user_agent,
	)


@router.post("", response_model=FileItemResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
	request: Request,
	uploaded_file: UploadFile = File(...),
	vault_type: str = Form(default="private"),
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileItemResponse:
	ip_address, user_agent = _request_metadata(request)
	content = await uploaded_file.read()
	return service.upload_file(
		current_context,
		filename=uploaded_file.filename,
		content_type=uploaded_file.content_type,
		content=content,
		vault_type=vault_type,
		ip_address=ip_address,
		user_agent=user_agent,
	)


@router.get("/approvals", response_model=FileListResponse)
def list_approvals(
	request: Request,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileListResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.list_pending_approvals(
		current_context,
		page=page,
		page_size=page_size,
		ip_address=ip_address,
		user_agent=user_agent,
	)


@router.get("/publish-requests", response_model=PublishRequestListResponse)
def list_publish_requests(
	request: Request,
	status: str | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> PublishRequestListResponse:
	return service.list_publish_requests(
		current_context,
		status=status,
		page=page,
		page_size=page_size,
	)


@router.post("/publish-requests/{request_id}/approve", response_model=PublishRequestResponse)
def approve_publish_request(
	request_id: str,
	request: Request,
	payload: FileApproveRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> PublishRequestResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.review_publish_request(
		current_context,
		request_id,
		approved=True,
		note=payload.note,
		ip_address=ip_address,
		user_agent=user_agent,
	)


@router.post("/publish-requests/{request_id}/reject", response_model=PublishRequestResponse)
def reject_publish_request(
	request_id: str,
	request: Request,
	payload: FileRejectRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> PublishRequestResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.review_publish_request(
		current_context,
		request_id,
		approved=False,
		note=payload.note,
		ip_address=ip_address,
		user_agent=user_agent,
	)


@router.get("/{file_id}", response_model=FileItemResponse)
def get_file(
	file_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileItemResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.get_file(current_context, file_id, ip_address=ip_address, user_agent=user_agent)


@router.get("/{file_id}/download")
def download_file(
	file_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> StreamingResponse:
	ip_address, user_agent = _request_metadata(request)
	result: FileDownloadResult = service.download_file(current_context, file_id, ip_address=ip_address, user_agent=user_agent)
	headers = {
		"Content-Disposition": f'attachment; filename="{result.record.original_name}"',
		"X-File-SHA256": result.record.sha256,
	}
	return StreamingResponse(BytesIO(result.content), media_type=result.record.mime_type, headers=headers)


@router.post("/{file_id}/approve", response_model=FileItemResponse)
def approve_file(
	file_id: str,
	request: Request,
	payload: FileApproveRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileItemResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.approve_file(current_context, file_id, note=payload.note, ip_address=ip_address, user_agent=user_agent)


@router.post("/{file_id}/reject", response_model=FileItemResponse)
def reject_file(
	file_id: str,
	request: Request,
	payload: FileRejectRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileItemResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.reject_file(current_context, file_id, note=payload.note, ip_address=ip_address, user_agent=user_agent)


@router.post("/{file_id}/request-publish", response_model=PublishRequestResponse)
def request_publish(
	file_id: str,
	request: Request,
	payload: RequestPublishRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> PublishRequestResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.request_publish(current_context, file_id, target=payload.target, ip_address=ip_address, user_agent=user_agent)


@router.patch("/{file_id}", response_model=FileItemResponse)
def admin_update_file(
	file_id: str,
	request: Request,
	payload: FileAdminUpdateRequest,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileItemResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.admin_update_file(current_context, file_id, payload, ip_address=ip_address, user_agent=user_agent)


@router.delete("/{file_id}", response_model=FileDeleteResponse)
def delete_file(
	file_id: str,
	request: Request,
	current_context=Depends(get_current_auth_context),
	service: FileService = Depends(get_file_service),
) -> FileDeleteResponse:
	ip_address, user_agent = _request_metadata(request)
	return service.delete_file(current_context, file_id, ip_address=ip_address, user_agent=user_agent)
