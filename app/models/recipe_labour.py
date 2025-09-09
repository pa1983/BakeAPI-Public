# app/models/recipe_labour.py

from typing import Optional
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship

# Use string literals for type hints to avoid circular import errors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .recipe import Recipe
    from .labourer import Labourer
    from .labour_category import LabourCategory


class RecipeLabourBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    recipe_id: int = Field(foreign_key="recipe.recipe_id")
    labourer_id: int = Field(foreign_key="labourer.id")
    labour_minutes: Decimal = Field(
        default=Decimal("0.0"),
        max_digits=10,
        decimal_places=4,
        description="Number of minutes for the labour entry item."
    )
    labour_category_id: int = Field(
        foreign_key="labour_category.id",
        description="Type of labour for grouping purposes, e.g., prep, production, clean-up."
    )
    description: str = Field(
        max_length=255,
        description=(
            "Description of the labour covered by the entry, relating to an action on the full batch. "
            "E.g., knead dough, clean mixer, weigh out ingredients."
        )
    )
    sort_order: int = Field(default=10)


class RecipeLabour(RecipeLabourBase, table=True):
    """
    The main table model for recipe labour.
    Defines man-hours for prep, production, and clean-up, broken down by skill level.
    """
    __tablename__ = "recipe_labour"

    id: int = Field(default=None, primary_key=True)
    organisation_id: Optional[int] = Field(
        default=None,
        foreign_key="organisation.organisation_id"
    )

    # --- Relationships ---
    recipe: "Recipe" = Relationship()
    labourer: "Labourer" = Relationship()
    labour_category: "LabourCategory" = Relationship()
    organisation: "Organisation" = Relationship()


class RecipeLabourRead(RecipeLabourBase):
    """
    Model for reading a recipe labour entry, includes the primary key.
    """
    id: int


class RecipeLabourCreate(RecipeLabourBase):
    """
    Model for creating a new recipe labour entry.
    """
    pass


class RecipeLabourUpdate(SQLModel):
    """
    Model for updating an existing recipe labour entry. All fields are optional.
    """
    labourer_id: Optional[int] = None
    labour_minutes: Optional[Decimal] = None
    labour_category_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None