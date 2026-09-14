from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.security.dependencies import get_current_user, require_role
from app.services import company_service
from app.services.company_service import get_company
from app.utils.pagination import PageParams, pagination_params

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CompanyRead])
def list_companies(
    search: Optional[str] = Query(default=None),
    page_params: PageParams = Depends(pagination_params),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> PaginatedResponse:
    companies, total = company_service.list_companies(
        db, offset=page_params.offset, limit=page_params.page_size, search=search
    )
    return PaginatedResponse[CompanyRead](
        items=companies, total=total, page=page_params.page, page_size=page_params.page_size
    )


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> CompanyRead:
    return company_service.create_company(db, current_user, payload)


@router.get("/{company_id}", response_model=CompanyRead)
def read_company(
    company_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CompanyRead:
    return get_company(db, company_id)


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> CompanyRead:
    company = get_company(db, company_id)
    return company_service.update_company(db, current_user, company, payload)
