from .crud_factory import create_crud_router
from app.models.brand import Brand, BrandCreate, BrandRead, BrandUpdate

brandRouter = create_crud_router(
    model=Brand,
    create_schema=BrandCreate,
    read_schema=BrandRead,
    update_schema=BrandUpdate,
    tags=["Brand"],
    pk_field_name="brand_id",
    name_field="brand_name"
)

