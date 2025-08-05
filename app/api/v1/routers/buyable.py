from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Body, Depends

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, select, and_, or_
from starlette import status

from app.api.v1.routers.brand import brandRouter
from app.api.v1.routers.supplier import supplierRouter
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user

from app.models.buyable import BuyableRead, Buyable
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.user import User

buyableRouter: APIRouter = APIRouter()

buyableRouter.include_router(
    brandRouter,
    prefix="/brand",
    tags=["Brand"]
)

buyableRouter.include_router(
    supplierRouter,
    prefix="/supplier",
    tags=["Supplier"]
)

# =======BUYABLE======== #~
# GET all by org

# GET one by ID

# DELETE one by ID

# PATCH one by ID

# POST new

