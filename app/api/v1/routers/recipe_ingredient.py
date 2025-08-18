from fastapi import APIRouter

from app.api.v1.routers.crud_factory import create_crud_router
from app.models import RecipeIngredient
from app.models.recipe_ingredient import RecipeIngredientCreate, RecipeIngredientRead, RecipeIngredientUpdate

recipeIngredientRouter: APIRouter = create_crud_router(
    model=RecipeIngredient,
    create_schema=RecipeIngredientCreate,
    read_schema=RecipeIngredientRead,
    update_schema=RecipeIngredientUpdate,
    pk_field_name="id",
    name_field="recipe_ingredient_link"
)

