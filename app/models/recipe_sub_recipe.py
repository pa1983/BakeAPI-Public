# /models/recipe_sub_recipe.py

from typing import TYPE_CHECKING, Optional
from decimal import Decimal
from sqlmodel import Field, Relationship, SQLModel

# Use TYPE_CHECKING to avoid circular import errors
if TYPE_CHECKING:
    from .recipe import Recipe, RecipeRead
    from .uom import UnitOfMeasure, UnitOfMeasureRead


class RecipeSubRecipeBase(SQLModel):
    """
    Base model for a sub-recipe link, containing all core fields.
    """
    parent_recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        description="ID of the recipe that contains the sub-recipe."
    )
    sub_recipe_id: int = Field(
        foreign_key="recipe.recipe_id",
        description="ID of the recipe being used as a sub-recipe ingredient."
    )
    quantity: Decimal = Field(
        max_digits=18,
        decimal_places=10,
        description="Quantity of the sub-recipe used in the parent recipe."
    )
    uom_id: int = Field(
        foreign_key="unit_of_measure.uom_id",
        description="ID for the unit of measure for the quantity."
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2550,
        description="Optional notes about this sub-recipe's use."
    )
    sort_order: int = Field()


class RecipeSubRecipe(RecipeSubRecipeBase, table=True):
    """
    Represents an entry in the recipe_sub_recipe join table.
    """
    __tablename__ = "recipe_sub_recipe"

    id: Optional[int] = Field(default=None, primary_key=True)

    organisation_id: Optional[int] = Field(
        default=None,
        foreign_key="organisation.organisation_id"
    )


    parent_recipe: Optional["Recipe"] = Relationship(
        back_populates="sub_recipe_links",
        sa_relationship_kwargs={"foreign_keys": "[RecipeSubRecipe.parent_recipe_id]"}
    )

    sub_recipe: Optional["Recipe"] = Relationship(
        back_populates="parent_recipe_links",
        sa_relationship_kwargs={"foreign_keys": "[RecipeSubRecipe.sub_recipe_id]"}
    )

    unit_of_measure: Optional["UnitOfMeasure"] = Relationship()
    organisation: "Organisation" = Relationship()


class RecipeSubRecipeCreate(RecipeSubRecipeBase):
    """
    Model for creating a new RecipeSubRecipe link via the API.
    ID is not required as it's auto-generated.
    """
    pass


class RecipeSubRecipeRead(RecipeSubRecipeBase):
    """
    Model for reading a RecipeSubRecipe link from the API.
    Includes the auto-generated ID.
    """
    id: int


class RecipeSubRecipeUpdate(SQLModel):
    """
    Model for updating a RecipeSubRecipe link via a PATCH request.
    All fields are optional.
    """
    sub_recipe_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    uom_id: Optional[int] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class RecipeSubRecipeReadWithJoins(RecipeSubRecipeRead):
    """
    Extends the Read model to include related objects for detailed API responses.
    Typically used when fetching a parent recipe to show its ingredients.
    """
    sub_recipe: Optional["RecipeRead"] = None
    unit_of_measure: Optional["UnitOfMeasureRead"] = None