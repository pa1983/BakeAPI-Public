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
from app.models.user import User

supplierRouter: APIRouter = APIRouter()


element_type = 'Supplier'