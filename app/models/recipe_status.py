# probably won't need update/edit ability on this, just read since it's being used as an enum
# but useful to have for completeness if decide to implement in admin functionality in future

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Use a string literal for the type hint to avoid circular import errors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.recipe import Recipe


class RecipeStatusBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    recipe_status_name: str = Field(max_length=255)
    recipe_status_description: str = Field(default="", max_length=255)


class RecipeStatus(RecipeStatusBase, table=True):
    """
    The main table model for a recipe status.
    """
    __tablename__ = "recipe_status"
    recipe_status_id: Optional[int] = Field(default=None, primary_key=True)

    # One-to-many relationship to the Recipe model.
    # The 'back_populates' string must match the relationship
    # attribute name on the Recipe model.
    recipes: List["Recipe"] = Relationship(back_populates="recipe_status")


class RecipeStatusRead(RecipeStatusBase):
    """
    Model for reading a recipe status, includes the primary key.
    """
    recipe_status_id: int


class RecipeStatusCreate(RecipeStatusBase):
    """
    Model for creating a new recipe status.
    """
    pass


class RecipeStatusUpdate(SQLModel):
    """
    Model for updating an existing recipe status. All fields are optional.
    """
    recipe_status_name: Optional[str] = None
    recipe_status_description: Optional[str] = None
