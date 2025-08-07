# app/routers/brand.py

from pydantic import BaseModel
from typing import Optional
from .crud_factory import create_crud_router
from app.models.brand import Brand, BrandCreate, BrandRead

# 1. Define the specific model for PATCH updates
class BrandUpdate(BaseModel):
    brand_name: Optional[str] = None
    notes: Optional[str] = None

# 2. Call the factory with your models and configuration
brandRouter = create_crud_router(
    model=Brand,
    create_schema=BrandCreate,
    read_schema=BrandRead,
    update_schema=BrandUpdate,
    prefix="",
    tags=["Brands"],
    pk_field_name="brand_id",
    name_field="brand_name"
)