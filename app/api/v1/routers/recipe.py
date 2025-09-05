from datetime import datetime
from http.client import HTTPException
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.api.v1.routers.crud_factory import create_crud_router
from app.core.logging_config import logger
from app.database.session import get_session, engine
from app.dependencies.user_dependencies import get_current_user
from app.models import Recipe, RecipeIngredient, RecipeSubRecipe
from app.models.common import ApiResponse
from app.models.recipe import RecipeCreate, RecipeRead, RecipeUpdate
from app.models.recipeElements import RecipeElement, IngredientElement, LabourElement, \
    SubRecipeElement  # and any other types later created
from app.models.recipe_cost_analysis import RecipeCostAnalysis
from app.models.recipe_labour import RecipeLabour
from app.models.user import User
from app.queries.recipe import recipeCostAnalysisQuery

recipeRouter: APIRouter = create_crud_router(
    model=Recipe,
    create_schema=RecipeCreate,
    read_schema=RecipeRead,
    update_schema=RecipeUpdate,
    pk_field_name="recipe_id",
    name_field="recipe_name"
)

@recipeRouter.get("/{recipe_id}/cost-analysis",
                  summary="Get cost analysis for single recipe",
                  response_model=ApiResponse[list[RecipeCostAnalysis]])
async def get_recipe_cost_analysis(recipe_id: int,
                                   date_point: str | None = Query(None, description="Date for cost analysis in YYYY-MM-DD format. Defaults to today."),
                                   db_session: Session = Depends(get_session),
                                   user: User = Depends(get_current_user)
                                   ):
    try:

        if not date_point: # default it to today where it's missing from params
            date_point = datetime.today().strftime("%Y-%m-%d")


        results: list[RecipeCostAnalysis] = get_recipe_cost_analysis(db_session, recipe_id, date_point,
                                                                     user.organisation_id)
        return ApiResponse(data=results,
                           message=f"Recipe cost analysis retrieved successfully for recipe id {recipe_id}")
    except Exception as e:
        logger.error(f"Error retrieving recipe cost analysis for recipe id {recipe_id}: {e}")
        raise HTTPException(f"Error retrieving recipe cost analysis for recipe id {recipe_id}")


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
    recipe = session.get(Recipe, recipe_id).where(Recipe.organisation_id == user.organisation_id)
    if not recipe:
        logger.error(f"Recipe with id {recipe_id} not found")
        raise HTTPException(detail=f"Recipe with id {recipe_id} not found", status_code=404)

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

    return ApiResponse(data=sorted_list, message=f"Recipe elements retrieved successfully for recipe id {recipe_id}")





def get_recipe_cost_analysis(session: Session, top_recipe_id: int, date_point: str, organisation_id: int) -> list[
    RecipeCostAnalysis]:
    """
    Executes the raw costing query and parses the results into a list of
    RecipeCostAnalysis objects.
    """
    params = {
        "top_recipe_id": top_recipe_id,
        "date_point": date_point,
        "organisation_id": organisation_id,
    }
    results = session.exec(recipeCostAnalysisQuery, params=params).fetchall()

    # The result of fetchall() is a list of tuples/rows.
    # We need to map these to our model to allow SQLModel to handle serialisation and keep type checking accurate

    analysis_list = [RecipeCostAnalysis(**row._mapping) for row in results]
    return analysis_list


if __name__ == '__main__':
    # This is a demonstration and requires a database connection to run.
    params = {
        "top_recipe_id": 8,
        "organisation_id": "2",
        "date_point": "2025-02-01"
    }
    with Session(engine) as session:
        get_recipe_cost_analysis(session, **params)
