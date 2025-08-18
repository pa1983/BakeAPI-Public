# from __future__ import annotations # Postpone evaluation of type hints to prevent circular import issues
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Relationship

class Organisation(SQLModel, table=True):
    organisation_id: Optional[int] = Field(default=None, primary_key=True)
    organisation_name: str = Field(max_length=255)

    roles: List["Role"] = Relationship(back_populates="organisation")
    # Define the back-populating relationship to Ingredient
    # The 'ingredients' here matches back_populates="ingredients" in Ingredient model
    # ingredients: List["Ingredient"] = Relationship(back_populates="organisation")
    images: List["Image"] = Relationship(back_populates="organisation")
    users: List["User"] = Relationship(back_populates="organisation")

class OrganisationRead(BaseModel):
    organisation_id: int
    organisation_name: str