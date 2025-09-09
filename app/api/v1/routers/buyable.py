
from fastapi import APIRouter

from app.api.v1.routers.brand import brandRouter
from app.api.v1.routers.crud_factory import create_crud_router
from app.api.v1.routers.supplier import supplierRouter

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