#ingredient.py
from __future__ import annotations # Postpone evaluation of type hints to prevent circular import issues

from typing import Optional, List
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field, Relationship

from app.models.ingredient_image import IngredientImage
from app.models.organisation import Organisation, OrganisationRead
from app.models.uom import unit_of_measure

class Ingredient(SQLModel, table=True):
    ingredient_id: int = Field(default=None, primary_key=True)
    ingredient_name: str = Field(max_length=50, unique=True, index=True)
    standard_uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    density: Optional[float] = Field(default=None)  # Corresponds to DECIMAL(18, 10)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")

    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                        nullable=False)
    modified_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                         sa_column_kwargs={"onupdate": "NOW()"})

    # note use of string literal below to avoid circular import errors if use direct class reference
    standard_uom: unit_of_measure = Relationship(back_populates="ingredients")
    organisation: Optional[Organisation] = Relationship(back_populates="ingredients")

    # Direct many-to-many relationship to Image via IngredientImage link model
    # 'images' is the new relationship attribute on Ingredient
    image_links: List["IngredientImage"] = Relationship(

        back_populates="ingredient" # relates the name of the relationship on the Image model
    )


class IngredientRead(SQLModel):
    ingredient_id: int
    ingredient_name: str
    standard_uom_id: int
    density: Optional[float]
    organisation_id: Optional[int]
    created_timestamp: datetime
    modified_timestamp: datetime

    standard_uom: unit_of_measure
    organisation: Optional[OrganisationRead]

    images: List["ImageRead"] = [] # Initialise as empty list for default serialization
