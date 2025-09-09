# app/models/labour_category.py

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

# Use a string literal for the type hint to avoid circular import errors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .organisation import Organisation


class LabourCategoryBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    name: str = Field(max_length=255)
    description: Optional[str] = Field(
        default=None,
        max_length=2550,
        description="Description of the category, might contain a list of tasks typically covered."
    )



class LabourCategory(LabourCategoryBase, table=True):
    """
    The main table model for a labour category.
    """
    __tablename__ = "labour_category"

    # Define the composite unique constraint for name and organisation_id
    __table_args__ = (
        UniqueConstraint("name", "organisation_id", name="uq_labour_category_organisation"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    organisation_id: Optional[int] = Field(
        default=None,
        foreign_key="organisation.organisation_id"
    )
    # Relationship to the Organisation model
    organisation: Optional["Organisation"] = Relationship()


class LabourCategoryRead(LabourCategoryBase):
    """
    Model for reading a labour category, includes the primary key.
    """
    id: int


class LabourCategoryCreate(LabourCategoryBase):
    """
    Model for creating a new labour category.
    """
    pass


class LabourCategoryUpdate(SQLModel):
    """
    Model for updating an existing labour category. All fields are optional.
    """
    name: Optional[str] = None
    description: Optional[str] = None