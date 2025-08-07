from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Body, Depends

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, select, and_, or_
from starlette import status

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.supplier import Supplier
from app.models.user import User

supplierRouter: APIRouter = APIRouter()

async def get_suppliers(session: Session = Depends(get_session),
                                user: User = Depends(get_current_user)) -> ApiResponse[Supplier]:
    suppliers = session.exec(
        select(Supplier).where(Supplier.organisation_id == user.organisation_id)
    ).all()
    return ApiResponse(data=suppliers, message="Suppliers retrieved successfully.", status_code=status.HTTP_200_OK)

element_type = 'Supplier'