from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...api.dependencies.auth import get_current_auth_context
from ...schemas.users import FloorItemResponse, FloorListResponse

router = APIRouter(prefix="/floors", tags=["floors"])


def _get_auth_repository(request: Request):
	return request.app.state.auth_repository


def _get_demo_org(request: Request):
	return request.app.state.auth_repository.get_demo_organization()


@router.get("", response_model=FloorListResponse)
def list_floors(
	request: Request,
	current_context=Depends(get_current_auth_context),
	repo=Depends(_get_auth_repository),
) -> FloorListResponse:
	floors = repo.list_floors(current_context.user.organization_id)
	return FloorListResponse(items=[FloorItemResponse.model_validate(f) for f in floors])
