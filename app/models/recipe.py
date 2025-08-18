# app/models/recipe.py

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import ConfigDict
from sqlalchemy import func
from sqlmodel import SQLModel, Field, Relationship

# Use string literals for type hints to avoid circular import errors
from typing import TYPE_CHECKING

from .recipe_labour import RecipeLabour

if TYPE_CHECKING:
    from .recipe_type import RecipeType, RecipeTypeRead
    from .product_type import ProductType, ProductTypeRead
    from .recipe_status import RecipeStatus, RecipeStatusRead
    from .organisation import Organisation, OrganisationRead
    from .uom import UnitOfMeasure, UnitOfMeasureRead
    # This import is now only for type checking
    from .recipe_ingredient import RecipeIngredient, RecipeIngredientReadWithDetails
    from .recipe_sub_recipe import RecipeSubRecipe

class RecipeBase(SQLModel):
    """
    Base model with fields common to create, update, and read models.
    """
    recipe_name: str = Field(max_length=255)
    recipe_description: Optional[str] = Field(default=None, max_length=2550)
    recipe_type_id: int = Field(foreign_key="recipe_type.recipe_type_id")
    product_type_id: int = Field(foreign_key="product_type.product_type_id")
    recipe_status_id: int = Field(foreign_key="recipe_status.recipe_status_id")
    recipe_uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    version: int = Field(default=1)
    effective_from_date: Optional[datetime] = None
    effective_to_date: Optional[datetime] = None
    is_current: bool = Field(default=True)
    previous_recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.recipe_id")
    notes: Optional[str] = Field(default=None, max_length=2550)
    version_notes: Optional[str] = Field(default=None, max_length=2550)
    recipe_quantity: Decimal = Field(..., max_digits=8, decimal_places=3)
    yield_percentage: Decimal = Field(default=100.0, max_digits=8, decimal_places=3)


class Recipe(RecipeBase, table=True):
    """
    The main table model for a recipe.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    recipe_id: Optional[int] = Field(default=None, primary_key=True)

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
    recipe_type: "RecipeType" = Relationship(back_populates="recipes")
    product_type: "ProductType" = Relationship(back_populates="recipes")
    recipe_status: "RecipeStatus" = Relationship(back_populates="recipes")
    organisation: Optional["Organisation"] = Relationship()
    recipe_uom: "UnitOfMeasure" = Relationship()

    ingredients: List["RecipeIngredient"] = Relationship(back_populates="recipe")
    labour_entries: List["RecipeLabour"] = Relationship(back_populates="recipe")
    # to allow for tracking recipe versions, there's a previous version field in the recipe table
    # This necessitates the self-referring pattern, below, to
    previous_version: Optional["Recipe"] = Relationship(
        back_populates="next_versions",
        sa_relationship_kwargs=dict(
            remote_side="Recipe.recipe_id",
            foreign_keys="Recipe.previous_recipe_id"
        )
    )
    next_versions: List["Recipe"] = Relationship(back_populates="previous_version")

    # Defines the list of sub-recipes that make up THIS recipe.
    # It links to the 'RecipeSubRecipe' table where this recipe is the 'parent'.
    # using sa_relationship_kwargs as SQLModel doesn't have its own handlers for this functionality, so have
    # to fall back on SQL Alc functions.
    sub_recipe_links: List["RecipeSubRecipe"] = Relationship(
        back_populates="parent_recipe",
        sa_relationship_kwargs={"foreign_keys": "[RecipeSubRecipe.parent_recipe_id]"}
    )

    # Defines the list of parent recipes where THIS recipe is used as an ingredient.
    # It links to the 'RecipeSubRecipe' table where this recipe is the 'sub_recipe'.
    parent_recipe_links: List["RecipeSubRecipe"] = Relationship(
        back_populates="sub_recipe",
        sa_relationship_kwargs={"foreign_keys": "[RecipeSubRecipe.sub_recipe_id]"}
    )



class RecipeRead(RecipeBase):
    recipe_id: int
    created_timestamp: datetime
    modified_timestamp: datetime


class RecipeReadWithDetails(RecipeRead):
    recipe_type: "RecipeTypeRead"
    product_type: "ProductTypeRead"
    recipe_status: "RecipeStatusRead"
    organisation: Optional["OrganisationRead"] = None
    recipe_uom: "UnitOfMeasureRead"
    ingredients: List["RecipeIngredientReadWithDetails"] = []


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(RecipeBase):

    """
    Model for updating an existing recipe
    All fields are optional to allow the class to be used to validate allowable field names, types and values
    """
    recipe_name: Optional[str] = Field(default=None, max_length=255)
    recipe_description: Optional[str] = Field(default=None, max_length=2550)
    recipe_type_id: Optional[int] = Field(default=None, foreign_key="recipe_type.recipe_type_id")
    product_type_id: Optional[int] = Field(default=None, foreign_key="product_type.product_type_id")
    recipe_status_id: Optional[int] = Field(default=None, foreign_key="recipe_status.recipe_status_id")
    recipe_uom_id: Optional[int] = Field(default=None, foreign_key="unit_of_measure.uom_id")
    version: Optional[int] = Field(default=None)
    effective_from_date: Optional[datetime] = Field(default=None)
    effective_to_date: Optional[datetime] = Field(default=None)
    is_current: Optional[bool] = Field(default=None)
    previous_recipe_id: Optional[int] = Field(default=None, foreign_key="recipe.recipe_id")
    notes: Optional[str] = Field(default=None, max_length=2550)
    version_notes: Optional[str] = Field(default=None, max_length=2550)
    recipe_quantity: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=3)
    yield_percentage: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=3)

