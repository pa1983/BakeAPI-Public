from pydantic import BaseModel
from typing import Optional
from .crud_factory import create_crud_router
from app.models.brand import Brand, BrandCreate, BrandRead

class BrandUpdate(BaseModel):
    brand_name: Optional[str] = None
    notes: Optional[str] = None

brandRouter = create_crud_router(
    model=Brand,
    create_schema=BrandCreate,
    read_schema=BrandRead,
    update_schema=BrandUpdate,
    prefix="",
    tags=["Brand"],
    pk_field_name="brand_id",
    name_field="brand_name"
)