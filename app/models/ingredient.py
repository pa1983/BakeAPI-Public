# ingredient.py
# from __future__ import annotations # Postpone evaluation of type hints to prevent circular import issues

from typing import Optional, List
from datetime import datetime, timezone

from pydantic import computed_field
from sqlmodel import SQLModel, Field, Relationship

from app.models.ingredient_image import Ingredient_Image, Ingredient_ImageRead
from app.models.organisation import Organisation, OrganisationRead
from app.models.uom import unit_of_measure

from app.models.image import ImageRead


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
    organisation: Optional["Organisation"] = Relationship(back_populates="ingredients")

    # Direct many-to-many relationship to Image via IngredientImage link model
    # 'images' is the new relationship attribute on Ingredient
    image_links: List["Ingredient_Image"] = Relationship(

        back_populates="ingredient"  # relates the name of the relationship on the Image model
    )


class IngredientRead(SQLModel):
    ingredient_id: int
    ingredient_name: str
    standard_uom_id: int
    density: Optional[float]
    organisation_id: Optional[int]
    created_timestamp: datetime
    modified_timestamp: datetime

    standard_uom: unit_of_measure  # passes through a full unit of measure class object
    organisation: Optional[OrganisationRead]  # optionally passes through an organisation read instance

    image_links: List[Ingredient_ImageRead] = []

    # todo - consider??  image_links works as-is.  Do I need to use the computed_field and property?  Might be useful to flatten?  or just extra complexity?
    # todo -  the @property approach places the image in a sorted lost that can be iterated through, but the sort_order isn't explicitly displayed.  Which is best suited?
    # make decision once get react start page running

    @computed_field(return_type=List[
        ImageRead])  # Pydantic decorator - used to define a property whose value is dynamically computed from other fields in the model (in this case, after then main data is loaded)
    @property  # makes the images function accessible as if it were a class attribute
    def images(self) -> List[ImageRead]:
        sorted_image_links = sorted(self.image_links, key=lambda link: link.sort_order)  # apply sort order
        return [link.image for link in sorted_image_links if
                link.image]  # return only the image instance, in a sorted list


class IngredientListRead(SQLModel):
    ingredients: List[IngredientRead]
