# app/models/__init__.py

"""
This file centralises all model imports.

By importing all table models here to ensure that SQLAlchemy's registry
is fully populated before any relationships are configured to fix
the circular dependency errors that can occur when models reference each other.

"""

from .uom import UnitOfMeasure
from .organisation import Organisation
from .image import Image
from .ingredient_image import Ingredient_Image
from .recipe_type import RecipeType
from .product_type import ProductType
from .recipe_status import RecipeStatus
from .recipe_ingredient import RecipeIngredient, RecipeIngredientRead
from .recipe_sub_recipe import RecipeSubRecipe
from .ingredient import Ingredient
from .recipe import Recipe

__all__ = [
    "UnitOfMeasure",
    "Organisation",
    "Image",
    "Ingredient_Image",
    "RecipeType",
    "ProductType",
    "RecipeStatus",
    "Ingredient",
    "RecipeIngredient",
    "RecipeIngredientRead",
    "RecipeSubRecipe"
]
