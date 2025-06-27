from typing import Optional, List

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel, Relationship

class UnitOfMeasureBase(SQLModel):

    # name: str = Field(index=True, unique=True, max_length=50)
    # abbreviation: str = Field(index=True, unique=True, max_length=10)
    type: str = Field(max_length=20)
    # conversion_factor: float = Field(ge=0)  # Using float for DECIMAL, adjust precision as needed
    # is_base_unit: bool
    name: str
    abbreviation: str
    type: str
    conversion_factor: float
    is_base_unit: bool


class UnitOfMeasure(UnitOfMeasureBase, table=True):

    __tablename__ = "unit_of_measure"

    model_config = ConfigDict(arbitrary_types_allowed=True)
    uom_id: Optional[int] = Field(default=None, primary_key=True)

    ingredients: List["Ingredient"] = Relationship(
        back_populates="standard_uom"
    )

class UnitOfMeasureRead(UnitOfMeasureBase):
    # inherits all parent fields
    uom_id: Optional[int]
    model_config = ConfigDict(from_attributes=True)
    pass