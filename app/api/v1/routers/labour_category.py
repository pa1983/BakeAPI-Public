from fastapi import APIRouter

from app.api.v1.routers.crud_factory import create_crud_router
from app.models.labour_category import LabourCategory, LabourCategoryCreate, LabourCategoryRead, LabourCategoryUpdate

labourCategoryRouter: APIRouter = create_crud_router(
    model=LabourCategory,
    create_schema=LabourCategoryCreate,
    read_schema=LabourCategoryRead,
    update_schema=LabourCategoryUpdate)