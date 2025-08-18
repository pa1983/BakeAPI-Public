from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Body, Depends

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, select, and_, or_
from starlette import status

from app.api.v1.routers.brand import brandRouter
from app.api.v1.routers.crud_factory import create_crud_router
from app.api.v1.routers.supplier import supplierRouter
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user

from app.models.buyable import BuyableRead, Buyable, BuyableCreate, BuyableUpdate
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.user import User



buyableRouter: APIRouter = create_crud_router(
    model=Buyable,
    create_schema=BuyableCreate,
    read_schema=BuyableRead,
    update_schema=BuyableUpdate,
    prefix="",  #
    tags=["Buyable"],
    pk_field_name="id",
    name_field="item_name"
)

#  add the descendent routers to the buyable router once it's fully defined
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

