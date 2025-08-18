from fastapi import APIRouter

from app.api.v1.routers.crud_factory import create_crud_router
from app.models.recipe_labour import RecipeLabour, RecipeLabourCreate, RecipeLabourRead, RecipeLabourUpdate

recipeLabourRouter: APIRouter = create_crud_router(
    model=RecipeLabour,
    create_schema=RecipeLabourCreate,
    read_schema=RecipeLabourRead,
    update_schema=RecipeLabourUpdate
)