# app/models/recipe_ingredient.py

from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

# Use string literals for type hints to avoid circular import errors.
# All imports of other models MUST be inside this block.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .recipe import Recipe, RecipeRead
    from .ingredient import Ingredient, IngredientRead
    from .uom import UnitOfMeasure, UnitOfMeasureRead


class RecipeIngredientBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    recipe_id: int = Field(foreign_key="recipe.recipe_id")
    ingredient_id: int = Field(foreign_key="ingredient.ingredient_id")

    # CORRECTED: Use Python's Decimal type and SQLModel's specific arguments
    # for precision and scale. This avoids the conflicting type error.
    quantity: Decimal = Field(..., max_digits=10, decimal_places=4)

    uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    notes: Optional[str] = Field(max_length=2550)
    sort_order: int = Field(default=10)

class RecipeIngredient(RecipeIngredientBase, table=True):
    """
    The main table model for the recipe_ingredient link table.
    """
    __tablename__ = "recipe_ingredient"

    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredient"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    created_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    modified_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": func.now()}
    )
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")
    # --- Relationships ---
    # The relationships use string forward-references ("Recipe", "Ingredient")
    # which are resolved by SQLAlchemy after all models have been loaded.
    recipe: "Recipe" = Relationship(back_populates="ingredients")
    ingredient: "Ingredient" = Relationship(back_populates="recipe_links")
    uom: "UnitOfMeasure" = Relationship()


class RecipeIngredientRead(RecipeIngredientBase):
    id: int


class RecipeIngredientReadWithDetails(RecipeIngredientRead):
    recipe: "RecipeRead"
    ingredient: "IngredientRead"
    uom: "UnitOfMeasureRead"


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientUpdate(SQLModel):

    quantity: Optional[Decimal] = None
    uom_id: Optional[int] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None

