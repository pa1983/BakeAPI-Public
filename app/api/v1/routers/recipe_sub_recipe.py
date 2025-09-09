from fastapi import APIRouter

from app.api.v1.routers.crud_factory import create_crud_router
from app.models import RecipeSubRecipe
from app.models.recipe_sub_recipe import RecipeSubRecipeCreate, RecipeSubRecipeUpdate, RecipeSubRecipeRead

recipeSubRecipe: APIRouter = create_crud_router(
    model = RecipeSubRecipe,
    create_schema=RecipeSubRecipeCreate,
    read_schema=RecipeSubRecipeRead,
    update_schema=RecipeSubRecipeUpdate
)