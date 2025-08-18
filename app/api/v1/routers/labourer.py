from fastapi import APIRouter

from app.api.v1.routers.crud_factory import create_crud_router
from app.api.v1.routers.labour_category import labourCategoryRouter
from app.models.labourer import Labourer, LabourerCreate, LabourerRead, LabourerUpdate

labourerRouter: APIRouter = create_crud_router(
    model=Labourer,
    create_schema=LabourerCreate,
    read_schema=LabourerRead,
    update_schema=LabourerUpdate,
    prefix="", # will be defined in main.py to keep path definitions in one central location
)

labourerRouter.include_router(labourCategoryRouter, prefix="/labour_category")