from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlmodel import select, bindparam, Session

from app.api.v1.routers import organisation
from app.core.logging_config import logger
from app.database.session import get_session
from app.models.common import ApiResponse
from app.models.currency import Currency
from app.models.product_type import ProductTypeRead, ProductType
from app.models.recipe_status import RecipeStatusRead, RecipeStatus
from app.models.recipe_type import RecipeTypeRead, RecipeType
from app.models.supplier import Supplier
from app.models.uom import UnitOfMeasure

from app.core.auth import cognito_auth
from app.dependencies.user_dependencies import get_current_user
from app.models.user import User, Organisation, Title
from app.services import s3_handler
from app.services.s3_handler import delete_s3_object

# fetch list of UOMs, will be fed into state management in the app and used in drop downs
# etc when selecting a UOM for an ingredient/recipe/buyable item etc

CommonRouter: APIRouter = APIRouter()


# see below for depndancy injection of sqlmodel session
@CommonRouter.get("/uom",
                  status_code=status.HTTP_200_OK,  # pre-define the success status code.  Only gets overridden if there's an HTTP error thrown
                  response_model=List[UnitOfMeasure])
async def uom_get(session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user))->List[UnitOfMeasure]:
    # todo - come back and get get_user working - going to be fundamental to all subsequent queries
    # ,
    #               current_user: User = Depends(get_user)
    #               ) -> List[unit_of_measure]:
    """
    Get a list of all units of measure; will be stored in app/front-end state
    store for use in choosing UOM for recipes, ingredients, and used in
    front-end calculations
    
    :return: 
    """
    try:
        res =  session.exec(select(UnitOfMeasure)).all()

        return res
    except Exception as e:
        print(f"Error fetching units of measure: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@CommonRouter.get("/title",
                  status_code=status.HTTP_200_OK,
                  response_model=List[Title])

async def title_get(session: Session = Depends(get_session)):
    try:
        res = session.exec(select(Title).order_by(Title.sort_order)).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Title table not found")

    return res


@CommonRouter.get("/currency",
                  status_code=status.HTTP_200_OK,
                  response_model=ApiResponse[List[Currency]],
                  summary="Get a list of all currencies",
                  description="Get a list of all currencies in the database using schema *Currency*."
                              "Primary key field name is *currency_name*.")

async def get_currency(session: Session = Depends(get_session)) -> ApiResponse[List[Currency]]:
    try:
        res = session.exec(select(Currency).order_by(Currency.currency_name)).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Currency table not found")

    return ApiResponse(data=res, message="Currency list retrieved")

@CommonRouter.get("/supplier")
async def get_invoice_form_data(session: Session = Depends(get_session),
                                user: User = Depends(get_current_user))->List[Supplier]:
    try:
        suppliers = session.exec(
            select(Supplier).where(Supplier.organisation_id == user.organisation_id)
        ).all()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Supplier table not found")
    return suppliers

# todo - integrate user data viewer later - for now keep it out of the router.
# @CommonRouter.get("/user_info", response_model=User)
# async def user_info(current_user: User = Depends(get_current_user),
#                     session: Session = Depends(get_session)):
#     # check i have access to the session here as a result of calling it within get current user
#
#     organisation = (session.exec(select(Organisation).
#                                  where(Organisation.organisation_id == current_user.organisation_id))
#                     .first())
#     print(f'Org name: {organisation.organisation_name}')
#     return current_user

# todo - make different versions for different file upload types.  Specific version for image, invoice, price list etc
@CommonRouter.post("/file_upload")
async def file_upload_post(file: UploadFile = File(...)) -> ApiResponse[None]:
    try:
        s3_key = s3_handler.push_UploadFile_to_s3(file, directory="invoice")  # todo - consider enum-ing this
        logger.debug(f"File pushed to S3: {s3_key}")
        delete_s3_object(s3_key)
        return ApiResponse(data=None, message=f"File uploaded successfully {file.filename} with s3 key {s3_key}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error uploading file: {e}")




# recipe form information
@CommonRouter.get('/product_type')
async def get_product_type(session: Session = Depends(get_session),
                           ) -> ApiResponse[List[ProductTypeRead]]:
    try:
        res = session.exec(select(ProductType)).all()
        return ApiResponse(data=res,
                           message="Product Type list retrieved")
    except Exception as e:
        logger.exception(f"Error retrieving product type table: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error retrieving product type table")


@CommonRouter.get('/recipe_type')
async def get_recipe_type(session: Session = Depends(get_session),
                           ) -> ApiResponse[List[RecipeTypeRead]]:
    try:
        res = session.exec(select(RecipeType)).all()
        return ApiResponse(data=res,
                           message="Recipe Type list retrieved")
    except Exception as e:
        logger.exception(f"Error retrieving recipe type table: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           detail=f"Error retrieving recipe type table")

@CommonRouter.get('/recipe_status')
async def get_recipe_status(session: Session = Depends(get_session),
                          ) -> ApiResponse[List[RecipeStatusRead]]:
    try:
        res = session.exec(select(RecipeStatus)).all()
        return ApiResponse(data=res,
                           message="Recipe status list retrieved")
    except Exception as e:
        logger.exception(f"Error retrieving recipe status table: {e}")
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           detail=f"Error retrieving recipe status table")