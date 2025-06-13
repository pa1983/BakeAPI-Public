# check if the org id is either a match to the user, or null (denoting a generic entry)

from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database.session import get_session

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
                      response_model=IngredientRead)
async def get_ingredient(ingredient_id: int,
                         session: Session = Depends(get_session)
                         ) -> IngredientRead:
    print(f'getting ingredient data for ID: {ingredient_id}')
    # todo - add check for org ID to ensure matches if ingerdient Org ID is not null. Add testing where a custom ingredient is called from wrong org id
    # statement = (
    #     select(Ingredient)
    #     .select_from(Ingredient)
    #     .join(Ingredient_Image)
    #     .join(Image)
    #
    # )
    statement = (
        select(Ingredient)
        .where(Ingredient.ingredient_id == ingredient_id)
        .options(
            selectinload(Ingredient.image_links).selectinload(Ingredient_Image.image)  # image_links links image to the M:M joining table; ingredient_image.image does the same on the other side of the joining table
        )
    )
    res = (session.exec(
        statement
    )
           .first())

    # Pydantic's model_validate automatically handles the nested list of ImageRead due to the direct relationship

    ingredient_read_instance = IngredientRead.model_validate(res)

    return ingredient_read_instance

# todo - bear in mind that ingredient returned should be FUNCTIONALLY useful, i.e. include any image URLs, type descrtiptions etc.
# todo - pick up here and try to get an ingredient pulled by ID, then confirm that it matches the current user's org
