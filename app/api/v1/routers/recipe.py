from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.v1.routers.crud_factory import create_crud_router
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models import Recipe, RecipeIngredient, RecipeSubRecipe
from app.models.common import ApiResponse
from app.models.recipe import RecipeCreate, RecipeRead, RecipeUpdate
from app.models.recipeElements import RecipeElement, IngredientElement, LabourElement, \
    SubRecipeElement  # and any other types later created
from app.models.recipe_labour import RecipeLabour
from app.models.user import User

recipeRouter: APIRouter = create_crud_router(
    model=Recipe,
    create_schema=RecipeCreate,
    read_schema=RecipeRead,
    update_schema=RecipeUpdate,
    pk_field_name="recipe_id",
    name_field="recipe_name"
)

@recipeRouter.get("/{recipe_id}/elements",
                  response_model=ApiResponse[list[RecipeElement]],
                  summary="Get homogeneous list of recipe elements for a recipe id"
                  )
async def get_recipe_elements(recipe_id: int,
                              session: Session = Depends(get_session),
                              user: User = Depends(get_current_user)):
    """
    Retrieve homogeneous list of recipe elements for a specific recipe id
    :param recipe_id:
    :param session:
    :param user:
    :return:
    """
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        return ApiResponse(data=[], message=f"Recipe with id {recipe_id} not found", status_code=404)

## todo - add user org checks here
    ingredients_query = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
    ingredients = session.exec(ingredients_query).all()

    labour_query = select(RecipeLabour).where(RecipeLabour.recipe_id == recipe_id)
    labour_entries = session.exec(labour_query).all()

    sub_recipe_query = select(RecipeSubRecipe).where(RecipeSubRecipe.parent_recipe_id == recipe_id)
    sub_recipes = session.exec(sub_recipe_query).all()

    combined_list: List[RecipeElement] = []
    for ingredient in ingredients:
        # by apending the ingredientElement, we append the database response data with the element_type string literal 'ingredient' for use by the front end mapping function
        combined_list.append(IngredientElement(data=ingredient))

    for labour_entry in labour_entries:
        combined_list.append(LabourElement(data=labour_entry))

    for sub_recipe in sub_recipes:
        combined_list.append(SubRecipeElement(data=sub_recipe))

    sorted_list = sorted(combined_list, key=lambda element: element.data.sort_order)

    return ApiResponse(data=sorted_list, message=f"Recipe elements retrieved successfully for recipe id {recipe_id}", status_code=200)