from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlmodel import select, bindparam, Session

from app.api.v1.routers import organisation
from app.core.logging_config import logger
from app.database.session import get_session
from app.models.common import ApiResponse
from app.models.uom import unit_of_measure

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
                  response_model=List[unit_of_measure])
async def uom_get(session: Session = Depends(get_session),
                  current_user: User = Depends(get_current_user))->List[unit_of_measure]:
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
        res =  session.exec(select(unit_of_measure)).all()

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

@CommonRouter.get("/token")
async def token_get(cognito_token=Depends(cognito_auth.auth_required)):
    try:
        res = cognito_token
        return res
    except Exception as e:
        print(f"Error fetching units of measure: {e}")
        # TODO: Add proper error handling, e.g., raise HTTPException


@CommonRouter.get("/user_info", response_model=User)
async def user_info(current_user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    # check i have access to the session here as a result of calling it within get current user

    organisation = (session.exec(select(Organisation).
                                 where(Organisation.organisation_id == current_user.organisation_id))
                    .first())
    print(f'Org name: {organisation.organisation_name}')
    return current_user

# todo - make different versions for different file upload types.  Specific version for image, invoice, price list etc
@CommonRouter.post("/file_upload")
async def file_upload_post(file: UploadFile = File(...)) -> ApiResponse[None]:
    try:
        s3_key = s3_handler.push_UploadFile_to_s3(file, directory="invoice")  # todo - consider enum-ing this
        logger.debug(f"File pushed to S3: {s3_key}")
        delete_s3_object(s3_key)
        return ApiResponse(data=None, message=f"File uploaded successfully {file.filename} with s3 key {s3_key}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, message=f"Error uploading file: {e}")

