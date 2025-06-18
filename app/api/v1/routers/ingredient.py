# check if the org id is either a match to the user, or null (denoting a generic entry)

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_, or_

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user

from app.models.common import ApiResponse
from app.models.user import User
from app.models.ingredient import Ingredient, Ingredient_Image, IngredientRead
# come back to figure out ingredient read and how to handle it
from app.models.ingredient_image import *
from app.models.uom import *
from app.models.image import *
from app.models.user import *
from app.models.organisation import *

# /ingredient/
IngredientRouter: APIRouter = APIRouter()


@IngredientRouter.get("/{ingredient_id}",
                      status_code=status.HTTP_200_OK,
                      response_model=ApiResponse[IngredientRead])
async def get_ingredient(ingredient_id: int,
                         session: Session = Depends(get_session),
                         user: User = Depends(get_current_user)

                         ) -> ApiResponse[IngredientRead]:
    """
    Get a single ingredient by ID
    :param ingredient_id:
    :param session:
    :param user:
    :return:
    """
    print(f'getting ingredient data for ID: {ingredient_id}')
    organisation_id = 1  # todo - arhdcoded in for testing.  Make dynaic from current signed in user for prod
    # look up the ingredient ID, and confirm that it belongs to the org id OR is a generic for use by all users
    statement = (
        select(Ingredient)
        .where(
            and_(Ingredient.ingredient_id == ingredient_id,
                 or_(Ingredient.organisation_id == organisation_id,
                     Ingredient.organisation_id.is_(None)))
        )
        .options(
            selectinload(Ingredient.image_links).selectinload(Ingredient_Image.image)
            # image_links links image to the M:M joining table; ingredient_image.image does the same on the other side of the joining table
        )
    )
    res = (session.exec(
        statement
    )
           .first())

    # Pydantic's model_validate automatically handles the nested list of ImageRead due to the direct relationship

    ingredient_read_instance = IngredientRead.model_validate(res)

    return ApiResponse(data=ingredient_read_instance, message=f'Ingredient Found')

# todo - bear in mind that ingredient returned should be FUNCTIONALLY useful, i.e. include any image URLs, type descrtiptions etc.
# todo - pick up here and try to get an ingredient pulled by ID, then confirm that it matches the current user's org


# todo - endpoints to implement:
# ALL ingredients, paginated to avoid overloading front end if lats available
# FILTER - by name, type, organisation-owned
# both will return a list of IngredientRead

async def get_ingredients(session: Session = Depends(get_session)):
    pass