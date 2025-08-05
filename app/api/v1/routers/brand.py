from typing import Optional

import sqlalchemy
from fastapi import APIRouter, Body, Depends

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, select, and_
from starlette import status

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.brand import BrandCreate, Brand, BrandRead
from app.models.common import ApiResponse
from app.models.user import User

brandRouter: APIRouter = APIRouter()


element_type = 'Brand'

# =======BRAND======== #
@brandRouter.post("",
                    response_model=ApiResponse[BrandRead | None])
async def post_new(
        form_data: BrandCreate = Body(...),
        session: Session = Depends(get_session),
        user: User = Depends(get_current_user)
) -> ApiResponse[BrandRead | None]:
    try:
        from_form = form_data.model_dump()
        from_form['organisation_id'] = user.organisation_id
        new_element = Brand.model_validate(from_form)
        session.add(new_element)

    except Exception as e:
        return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Error validating your {element_type} data - nothing was created: {e}",
                           data=None)

    try:
        session.commit()
        session.refresh(new_element)
        response_element_read: BrandRead = BrandRead.model_validate(new_element)

    except (sqlalchemyIntegrityError, pymlsqlIntegrityError) as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                           message=f"""{element_type} {new_element.brand_name} already exists in your organisation. 
                           Please select the existing entry or choose a different name.""",
                           data=None)

    except Exception as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message=f"Error creating {element_type}: {e}",
                           data=None)

    return ApiResponse(data=response_element_read,
                       message=f"{element_type} {new_element.brand_name} created successfully",
                       status_code=status.HTTP_201_CREATED)


@brandRouter.get("/{id}",
                   response_model=ApiResponse[BrandRead | None])
async def get_by_id(id: int,
                    session: Session = Depends(get_session),
                    user: User = Depends(get_current_user)) -> ApiResponse[BrandRead | None]:
    element_from_db = session.exec(
        select(Brand).where(and_(
            Brand.brand_id == id,
            Brand.organisation_id == user.organisation_id))
    ).first()

    try:

        if not element_from_db:
            # Raise an HTTPException, FastAPI will handle formatting
            return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                               message=f"{element_type} with id {id} not found in your organisation.",
                               data=None)

        brand_read = BrandRead.model_validate(element_from_db)

        return ApiResponse(data=brand_read,
                           message=f"{element_type} '{brand_read.brand_name}' retrieved successfully",
                           status_code=status.HTTP_200_OK)

    except Exception as e:
        return ApiResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message=f"Error retrieving {element_type}: {e}",
                           data=None)

@brandRouter.get("/all")
async def get_full_list(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    f"""
    Get all {element_type}s for the current user's organisation.
    :param session:
    :param user:
    :return:
    """
    elements = session.exec(
        select(Brand).where(Brand.organisation_id == user.organisation_id).order_by(Brand.brand_name)).all()
    return ApiResponse(data=elements, message=f"{element_type} retrieved successfully", status_code=status.HTTP_200_OK)


@brandRouter.delete("/{id}",
                      response_model=ApiResponse[None])
async def delete(id: int,
                 session: Session = Depends(get_session),
                 user: User = Depends(get_current_user)):
    element_to_delete = session.exec(
        select(Brand).where(and_(
            Brand.brand_id == id,
            Brand.organisation_id == user.organisation_id))
    ).first()

    if not element_to_delete:
        return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                           message=f"{element_type} with id {id} not found.",
                           data=None)

    element_name = element_to_delete.brand_name  # Store name before deleting

    try:
        session.delete(element_to_delete)
        session.commit()
    except Exception as e:
        # e.g. if a foreign key constraint prevents deletion
        session.rollback()
        return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                           message=f"Could not delete {element_type} '{element_name}'. Error: {e}",
                           data=None)

    return ApiResponse(data=None,
                       message=f"{element_type} '{element_name}' deleted",
                       status_code=status.HTTP_200_OK)



class UpdatedElement(BaseModel):
    # list of fields allowed to be updated by patch
    brand_name: Optional[str] = None  # need a default value here, otherwise setting will fail during model_validate
    notes: Optional[str] = None

@brandRouter.patch("/{id}",
                     response_model=ApiResponse[BrandRead])
async def update_field(
        id: int,
        update_data: UpdatedElement = Body(...),
        session: Session = Depends(get_session),
        user: User = Depends(get_current_user),
):
    element_to_update = session.exec(
        select(Brand).where(and_(Brand.brand_id == id, Brand.organisation_id == user.organisation_id))
    ).first()

    if not element_to_update:
        return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                           message=f"{element_type} with id {id} not found.",
                           data=None)

    # Get the update data, excluding any fields that were not set in the request,
    # to ensure that user hasn't sent a request to modify a field that should not be modified (e.g. ID)
    update_dict = update_data.model_dump(exclude_unset=True)

    if not update_dict:
        return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST,
                           message="No update data provided.",
                           data=None)

    # Safely update the model's attributes
    for key, value in update_dict.items():
        setattr(element_to_update, key, value)

    try:
        session.add(element_to_update)
        session.commit()
        session.refresh(element_to_update)
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                           message=f"Update failed. A {element_type} with that name may already exist. {e}",
                           data=None)

    except Exception as e:
        session.rollback()
        return ApiResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message=f"An error occurred while updating the {element_type}: {e}",
                           data=None)

    updated_element_read = BrandRead.model_validate(element_to_update)

    return ApiResponse(data=updated_element_read,
                       message=f"{element_type} '{updated_element_read.brand_name}' updated successfully.",
                       status_code=status.HTTP_200_OK)
