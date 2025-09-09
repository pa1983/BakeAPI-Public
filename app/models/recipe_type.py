# app/models/recipe_type.py

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Use a string literal for the type hint to avoid circular import errors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .recipe import Recipe


class RecipeTypeBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    recipe_type: str = Field(max_length=255)
    description: str = Field(default="", max_length=255)


class RecipeType(RecipeTypeBase, table=True):
    """
    The main table model for a recipe type.
    """
    __tablename__ = "recipe_type"
    recipe_type_id: Optional[int] = Field(default=None, primary_key=True)

    # One-to-many relationship to the Recipe model.
    recipes: List["Recipe"] = Relationship(back_populates="recipe_type")


class RecipeTypeRead(RecipeTypeBase):
    """
    Model for reading a recipe type, includes the primary key.
    """
    recipe_type_id: int


class RecipeTypeCreate(RecipeTypeBase):
    """
    Model for creating a new recipe type.
    """
    pass


class RecipeTypeUpdate(SQLModel):
    """
    Model for updating an existing recipe type. All fields are optional.
    """
    recipe_type: Optional[str] = None
    description: Optional[str] = None
