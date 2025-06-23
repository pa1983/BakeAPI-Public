# check if the org id is either a match to the user, or null (denoting a generic entry)
import os

from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.ext.sqlmodel import paginate as sqlmodel_paginate # SQLModel-specific paginate

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_, or_

from app.core.logging_config import logger
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user

from app.models.common import ApiResponse
from app.models.user import User
from app.models.ingredient import Ingredient, Ingredient_Image, IngredientRead, IngredientListRead
# come back to figure out ingredient read and how to handle it
from app.models.ingredient_image import *
from app.models.uom import *
from app.models.image import *
from app.models.user import *
from app.models.organisation import *
from app.services import s3_handler
from app.dependencies.user_dependencies import get_current_user

# /ingredient/
IngredientRouter: APIRouter = APIRouter()


# todo - endpoints to implement:
# ALL ingredients, paginated to avoid overloading front end if lats available
# FILTER - by name, type, organisation-owned
# both will return a list of IngredientRead

def print_location():
    print("Got here")

@IngredientRouter.get("/ingredients", response_model=Page[IngredientRead])
async def get_ingredients(
        tst = Depends(print_location),
        session: Session = Depends(get_session),
                          user: User = Depends(get_current_user),
                          ingredient_name: Optional[str] = Query(None, description="Filter ingredients by name (case insensative)"),
                          own_organisation: Optional[bool] = Query(None, description="Show only ingredients that belong to user's organisation")
                          # todo - add more filter types, e.g. ingredient type?  ONLY those owned by organisation (not NONE)
                            # todo - add auth required - disabled for testing
                          ):
    """
    Get all ingredients available to current signed in user.
    Returns nested objects, so each ingredient instance contains any available photos and UOM details

    :param own_organisation: Boolean - filter results to only show user their own organisation's custom ingredients (no system generics)
    :param ingredient_name: Filter response for insensative contains ingredient_name in ingredient_name
    :param session:
    :param user:

    Additional params available for pagination - page, size

    :return:


    """
    user = User(organisation_id=1, user_id=1)
    user.organisation_id = 1;
    # todo - break out statements into separte file -will make query testing simpler and keep this tidier
    # logger.debug(f"Getting ingredients.  Org ID {user.organisation_id}")
    statement = (
        select(Ingredient)

        .options(
            selectinload(Ingredient.image_links).selectinload(Ingredient_Image.image)
            # image_links links image to the M:M joining table; ingredient_image.image does the same on the other side of the joining table
        )
    )

    # filtering logic based on parameters
    if ingredient_name:
        statement = statement.where(Ingredient.ingredient_name.ilike(f"%{ingredient_name}%"))  # ilike for case-insensative comparison. %{}% for 'contains' search

    if own_organisation:
        statement = statement.where(Ingredient.organisation_id == user.organisation_id)
    else:
        statement = statement.where(
            or_(Ingredient.organisation_id == user.organisation_id,
                Ingredient.organisation_id.is_(None)))
    # Take the built statement, and pass to sqlmodel_paginate, along with the current DB session, to send paginated results

    # res = (session.exec(statement).all())
    # Take the list of ingredient objects, and run model validate.  Need to pass in the list as a dict with key
    # 'ingredients' to match the name of the field found in IngredientListRead
    # ingredients: IngredientListRead = IngredientListRead.model_validate({"ingredients": res})
    # return ingredients
    return sqlmodel_paginate(session, statement)


@IngredientRouter.get("/id/{ingredient_id}",
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


# todo - cosider nesting these further in their own .py file to keep code tidy - ingredient will be big enough
@IngredientRouter.post("/image/upload")
async def image_upload_post(file: UploadFile = File(...),
                            caption: str = Form(...),
                            alt_text: str = Form(...),
                            ingredient_id: int = Form(...),
                            session: Session = Depends(get_session),
                            user: User = Depends(get_current_user)
                            ) -> ApiResponse[None]:
    """
    Upload an image file to S3 and log necessary metadata to database.
    Build links to ingredients table

    :param file: a FastAPI UploadFile instance
    :param caption:
    :param alt_text:
    :param ingredient_id:
    :param session:
    :param user:
    :return:
    """
    try:
        s3_key = s3_handler.push_UploadFile_to_s3(file, directory="image")  # todo - consider enum-ing this
        logger.debug(f"File pushed to S3: {s3_key}")

        filename, extension = os.path.splitext(file.filename)

        image = Image(
            file_name=filename,
            file_ext=extension,
            file_size=file.size,
            mime_type=file.content_type,
            alt_text=alt_text,
            caption=caption,
            organisation_id=user.organisation_id,
            s3_key=s3_key)

        session.add(image)
        session.flush()  # flush in the image to get an ID for use in the link table
        logger.debug(image.image_id)

        ingredient_image_link = Ingredient_Image(ingredient_id=ingredient_id,
                                                 image_id=image.image_id)
        session.add(ingredient_image_link)
        session.commit()

        return ApiResponse(data=None, message=f"File uploaded successfully {file.filename} with s3 key {s3_key}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            details=f"Error uploading file - please try again: {e}")


@IngredientRouter.get("/image/delete")
async def image_delete_get(s3_object_key: str,
                           session: Session = Depends(get_session),
                           current_user: User = Depends(get_current_user)):
    # check that the user us linked to the image via organisation
    # delete the image
    s3_handler.delete_s3_object(s3_object_key)
    # delete related database objects: ingredient_image entry, image entry

    # send 201 response
