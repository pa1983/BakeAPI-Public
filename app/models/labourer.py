# app/models/labourer.py

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

# Use a string literal for the type hint to avoid circular import errors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .organisation import Organisation


class LabourerBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    name: str = Field(
        max_length=50,
        description="e.g. baker, head baker, barista, assistant, assistant baker"
    )
    description: Optional[str] = Field(default=None, max_length=255)



class Labourer(LabourerBase, table=True):
    """
    The main table model for a labourer type.
    Used to define a list of available labour types - null org_id denotes a standard system entry.
    """
    __tablename__ = "labourer"

    # Define the composite unique constraint
    __table_args__ = (
        UniqueConstraint("name", "organisation_id", name="UQ_labourer_organisation"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    organisation_id: Optional[int] = Field(
        default=None,
        foreign_key="organisation.organisation_id",
        description="Null for system standard entries. Org ID if it's a custom entry."
    )


    # Relationship to the Organisation model
    organisation: Optional["Organisation"] = Relationship()


class LabourerRead(LabourerBase):
    """
    Model for reading a labourer type, includes the primary key.
    """
    id: int


class LabourerCreate(LabourerBase):
    """
    Model for creating a new labourer type.
    """
    pass


class LabourerUpdate(SQLModel):
    """
    Model for updating an existing labourer type. All fields are optional.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    organisation_id: Optional[int] = None