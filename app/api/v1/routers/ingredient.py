
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
