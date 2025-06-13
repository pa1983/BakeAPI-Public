# from __future__ import annotations

from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship


class unit_of_measure(SQLModel, table=True):
    uom_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=50)
    abbreviation: str = Field(index=True, unique=True, max_length=10)
    type: str = Field(max_length=20)
    conversion_factor: float = Field(ge=0)  # Using float for DECIMAL, adjust precision as needed
    is_base_unit: bool

    ingredients: List["Ingredient"] = Relationship(
        back_populates="standard_uom"
    )

    class Config:
        # This can be used to add configurations specific to Pydantic if needed
        # For example, if you need to handle decimals specifically, you might use:
        # json_encoders = {Decimal: str}
        pass
