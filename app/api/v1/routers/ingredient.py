# check if the org id is either a match to the user, or null (denoting a generic entry)
import os

from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi_pagination import Page, paginate
from fastapi_pagination.ext.sqlmodel import paginate as sqlmodel_paginate  # SQLModel-specific paginate

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_, or_

from app.api.v1.routers.crud_factory import create_crud_router
from app.api.v1.routers.ingredient_buyable import ingredientBuyableRouter
from app.core.logging_config import logger
from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user

from app.models.common import ApiResponse
from app.models.user import User
from app.models.ingredient import Ingredient, Ingredient_Image, IngredientRead, IngredientBase, IngredientCreate, \
    IngredientUpdate
# come back to figure out ingredient read and how to handle it
from app.models.ingredient_image import *
from app.models.uom import *
from app.models.image import *
from app.models.user import *
from app.models.organisation import *
from app.services import s3_handler
from app.dependencies.user_dependencies import get_current_user

# /ingredient/
# IngredientRouter: APIRouter = APIRouter()


# todo - endpoints to implement:
# ALL ingredients, paginated to avoid overloading front end if lats available
# FILTER - by name, type, organisation-owned
# both will return a list of IngredientRead

IngredientRouter = create_crud_router(
    model=Ingredient,
    create_schema=IngredientCreate,
    read_schema=IngredientRead,
    update_schema=IngredientUpdate,
    prefix="",
    tags=["Ingredient"],
    pk_field_name="ingredient_id",
    name_field="ingredient_name",
    get_query_options=[
        selectinload(Ingredient.image_links).selectinload(Ingredient_Image.image),
    ],  # custom options to pull linked data for images via the image_links linking table (ingredient_image)
    parent_fk_field='ingredient_id',  # todo - when is this going to differ from pk_field_name?  ever?
    image_link_model=Ingredient_Image,
    attach_image_upload_endpoint=True

)

IngredientRouter.include_router(ingredientBuyableRouter, prefix="/link_buyable")

# todo - add cascading delete f linked buyables and images if an ingredient is deleted.  Additional query options?  Extra delete_query_optons optional parameter to ensure cascades are completed?

IngredientImageRouter = create_crud_router(
    model=Ingredient_Image,
    create_schema=Ingredient_ImageCreate,
    read_schema=Ingredient_ImageRead,
    update_schema=Ingredient_ImageUpdate,
    prefix="",
    tags=["Ingredient Image"],
    pk_field_name="id",
    filter_by_field="ingredient_id",  # this filters all the ingredient_image elements by ingredient id
    parent_fk_field="ingredient_id",
    name_field="ingredient_name",
    is_image_link_model=True
)




#
# #############IMAGE ENDPOINTS - special additions to the generic ingredient endpoints produced by the crud factory ####################
# # todo - cosider nesting these further in their own .py file to keep code tidy - ingredient will be big enough
# @IngredientRouter.post("/image/upload")
# async def image_upload_post(file: UploadFile = File(...),
#                             caption: str = Form(...),
#                             alt_text: str = Form(...),
#                             ingredient_id: int = Form(...),
#                             session: Session = Depends(get_session),
#                             user: User = Depends(get_current_user)
#                             ) -> ApiResponse[None]:
#     """
#     Upload an image file to S3 and log necessary metadata to database.
#     Build links to ingredients table
#
#     :param file: a FastAPI UploadFile instance
#     :param caption:
#     :param alt_text:
#     :param ingredient_id:
#     :param session:
#     :param user:
#     :return:
#     """
#     try:
#         s3_key = s3_handler.push_UploadFile_to_s3(file, directory="image")  # todo - consider enum-ing this
#         logger.debug(f"File pushed to S3: {s3_key}")
#
#         filename, extension = os.path.splitext(file.filename)
#
#         image = Image(
#             file_name=filename,
#             file_ext=extension,
#             file_size=file.size,
#             mime_type=file.content_type,
#             alt_text=alt_text,
#             caption=caption,
#             organisation_id=user.organisation_id,
#             s3_key=s3_key)
#
#         session.add(image)
#         session.flush()  # flush in the image to get an ID for use in the link table
#         logger.debug(image.image_id)
#
#         ingredient_image_link = Ingredient_Image(ingredient_id=ingredient_id,
#                                                  image_id=image.image_id)
#         session.add(ingredient_image_link)
#         session.commit()
#
#         return ApiResponse(data=None, message=f"File uploaded successfully {file.filename} with s3 key {s3_key}")
#     except Exception as e:
#         session.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail=f"Error uploading file - please try again: {e}")
#
#
# @IngredientRouter.get("/image/delete")
# async def image_delete_get(s3_object_key: str,
#                            session: Session = Depends(get_session),
#                            current_user: User = Depends(get_current_user)):
#     # check that the user us linked to the image via organisation
#     # delete the image
#     s3_handler.delete_s3_object(s3_object_key)
#     # delete related database objects: ingredient_image entry, image entry
#
#     # send 201 response
