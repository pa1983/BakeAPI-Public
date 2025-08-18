#product_type.py

# probably won't need update/edit ability on this, just read since it's being used as an enum
# but useful to have for completeness if decide to implement in admin functionality in future


from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Use a string literal for the type hint to avoid circular import errors  todo - go back and add this in other models where have imported unnecessary models for type-checking purposes
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.recipe import Recipe


class ProductTypeBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    product_type_name: str = Field(max_length=255)
    description: str = Field(default="", max_length=255)


class ProductType(ProductTypeBase, table=True):
    """
    The main table model for a product type.
    """
    __tablename__ = "product_type"
    product_type_id: Optional[int] = Field(default=None, primary_key=True)

    recipes: List["Recipe"] = Relationship(back_populates="product_type")


class ProductTypeRead(ProductTypeBase):
    """
    Model for reading a product type, includes the primary key.
    """
    product_type_id: int


class ProductTypeCreate(ProductTypeBase):
    """
    Model for creating a new product type.
    """
    pass


class ProductTypeUpdate(SQLModel):
    """
    Model for updating an existing product type. All fields are optional.
    """
    product_type_name: Optional[str] = None
    description: Optional[str] = None
