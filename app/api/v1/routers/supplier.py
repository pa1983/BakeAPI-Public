from app.api.v1.routers.crud_factory import create_crud_router
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.supplier import Supplier, SupplierCreate, SupplierRead, SupplierUpdate
from app.models.user import User

supplierRouter = create_crud_router(
    model=Supplier,
    create_schema=SupplierCreate,
    read_schema=SupplierRead,
    update_schema=SupplierUpdate,
    prefix="",
    tags=["Supplier"],
    pk_field_name="supplier_id",
    name_field="supplier_name"
)