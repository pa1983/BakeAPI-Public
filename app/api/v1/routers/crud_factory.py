# app/routers/crud_factory.py

from typing import Type, TypeVar, List, Optional, Any
import pathlib

from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, SQLModel, select, and_

from fastapi import APIRouter, Depends, Body, Request, File, UploadFile, Path, Form
from starlette import status
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.common import ApiResponse
from app.models.image import Image
from app.models.user import User
from app.services import s3_handler

# --- Generic Type Variables for strong typing - ensures that all models passed to the factory are SQLModel types---
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ImageLinkCreate(BaseModel):
    file_name: str
    file_ext: str
    alt_text: str | None = None
    caption: str | None = None


def parse_image_link_form_data(
        form_data_str: str = Form(..., alias="formData")
) -> ImageLinkCreate:
    """Parsed and validates the JSON string from the 'formData' for field accompanying the
    uploaded image file"""
    try:
        return ImageLinkCreate.model_validate_json(form_data_str)
    except ValidationError as e:
        return ApiResponse(data=None, message="Error validating form data", status_code=HTTP_400_BAD_REQUEST)


## original approach - replaced above with function to pull in additional query options for nested querying

def create_crud_router(
        *,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        read_schema: Type[ReadSchemaType],
        update_schema: Type[UpdateSchemaType],
        prefix: Optional[str] = "",
        # keep here for future flexability, but mostly prefer to define prefix when using the router in main to make it easier to see in an overview where all the routers point to
        tags: List[str] = [],
        pk_field_name: str = "id",  # The name of the primary key column, defaults to 'id'
        name_field: str = "name",  # A common field for user-friendly messages and log outputs
        get_query_options: Optional[List[Any]] = None,
        # optionally allow for additional query options, e.g. for nested queries
        filter_by_field: Optional[str] = None,  # The field name to optionally filter the /all endpoint,
        image_link_model: Optional[Type[ModelType]] = None,
        # if endpoint requires the option to upload images for the parent model, include an image link model to conditionally add delete all image links, images, and s3 objects when deleting the element
        parent_fk_field: Optional[str] = None,
        # required if passing an image link model so it knows what the field name of parent is to link to (image pk name always the same)
        attach_image_upload_endpoint: bool = False,
        # flag to add a POST endpoint to upload an image and add to link table  at /{id}/image/upload
        is_image_link_model: bool = False
) -> APIRouter:
    """
    Creates and returns a FastAPI APIRouter with full CRUD functionality.
    Assumes the model has an 'organisation_id' field for multi-tenancy data separation.
    """
    router = APIRouter(prefix=prefix, tags=tags)
    element_type = model.__name__

    # --- CREATE ---
    @router.post("", response_model=ApiResponse[read_schema | None], status_code=status.HTTP_201_CREATED)
    def create_new(
            form_data: create_schema = Body(...),
            session: Session = Depends(get_session),
            user: User = Depends(get_current_user)
    ):
        try:
            new_element = model.model_validate(form_data, update={'organisation_id': user.organisation_id})
            session.add(new_element)
            session.commit()
            session.refresh(new_element)
        except (sqlalchemyIntegrityError, pymlsqlIntegrityError) as e:
            session.rollback()
            print(e, e.args)
            return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                               message=f"{element_type} with that name or identifier already exists, or a foreign key does not exist.", data=None)

        except Exception as e:
            session.rollback()
            print(e, e.args)
            return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST, message=f"Error creating {element_type}: {e}",
                               data=None)

        return ApiResponse(data=read_schema.model_validate(new_element),
                           message=f"{element_type} created successfully.")

    # --- READ ALL (Updated to support optional filtering - initially to allow getting ingredient_buyable linked items from ingredient ID - ) ---
    @router.get("/all", response_model=ApiResponse[List[read_schema]])
    def get_all(
            request: Request,  # Added Request to access query params to get filter details, if present
            session: Session = Depends(get_session),
            user: User = Depends(get_current_user)
    ):
        # Start with the base statement for the user's organisation for
        statement = (
            select(model)
            .where(getattr(model, 'organisation_id') == user.organisation_id)
        )

        #  APPLY THE DYNAMIC FILTER IF CONFIGURED AND PROVIDED
        if filter_by_field:
            print(f'filtering by {filter_by_field}')
            # Check if a value for the filter field was passed in the URL query
            filter_value = request.query_params.get(
                filter_by_field)  # check the params for a query fieldname matching the filter_by_field passed in.  If this doesn't match, all results will be returied
            if filter_value is not None:
                try:
                    # Get the actual column attribute from the model
                    filter_column = getattr(model,
                                            filter_by_field)  # the query_param passed in must match the name of the filtered column or all results will be returned
                    # Add the filter to the query, assume the value is an integer.
                    statement = statement.where(filter_column == int(filter_value))
                except (AttributeError, ValueError):
                    # Silently ignore if the field doesn't exist or value is not an int - will just return all
                    pass

        # Apply ordering and custom eager loading options
        statement = statement.order_by(getattr(model, name_field, None))
        if get_query_options:
            statement = statement.options(*get_query_options)

        # print(f"statement: {statement}")
        elements = session.exec(statement).all()
        validated_elements = [read_schema.model_validate(el) for el in elements]
        return ApiResponse(data=validated_elements)

    # # --- READ ALL (Updated) ---
    # @router.get("/all", response_model=ApiResponse[List[read_schema]])
    # def get_all(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    #     statement = (
    #         select(model)
    #         .where(getattr(model, 'organisation_id') == user.organisation_id)
    #         .order_by(getattr(model, name_field, None))
    #     )
    #
    #     # --- APPLY CUSTOM OPTIONS ---
    #     if get_query_options:
    #         statement = statement.options(*get_query_options)
    #
    #     elements = session.exec(statement).all()
    #     validated_elements = [read_schema.model_validate(el) for el in elements]
    #     return ApiResponse(data=validated_elements)

    # --- READ ONE (Updated) ---
    @router.get("/{id}", response_model=ApiResponse[read_schema | None])
    def get_by_id(id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
        statement = select(model).where(
            and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id)
        )

        # --- APPLY CUSTOM OPTIONS ---
        if get_query_options:
            statement = statement.options(*get_query_options)

        element = session.exec(statement).first()

        if not element:
            return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                               message=f"{element_type} with id {id} not found.", data=None)

        return ApiResponse(data=read_schema.model_validate(element))

    # --- UPDATE (PATCH) ---
    @router.patch("/{id}", response_model=ApiResponse[read_schema | None])
    def update_partial(
            id: int,
            update_data: update_schema = Body(...),
            session: Session = Depends(get_session),
            user: User = Depends(get_current_user)
    ):
        element_to_update = session.exec(
            select(model).where(
                and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
        ).first()

        if not element_to_update:
            return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                               message=f"{element_type} with id {id} not found.", data=None)

        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST, message="No update data provided.", data=None)

        for key, value in update_dict.items():
            setattr(element_to_update, key, value)

        try:
            session.add(element_to_update)
            session.commit()
            session.refresh(element_to_update)
        except (sqlalchemyIntegrityError, pymlsqlIntegrityError):
            session.rollback()
            return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                               message=f"Update failed. A {element_type} with that name may already exist.", data=None)

        return ApiResponse(data=read_schema.model_validate(element_to_update),
                           message=f"{element_type} updated successfully.")

    # --- DELETE  ## conditionally checks for image_link_model to see if it also needs to remove matching image elements  ---
    @router.delete("/{id}", response_model=ApiResponse[None])
    def delete_by_id(id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
        element_to_delete = session.exec(
            select(model).where(
                and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
        ).first()

        if not element_to_delete:
            return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                               message=f"{element_type} with id {id} not found.", data=None)

        image_to_delete_from_s3 = None
        if is_image_link_model and hasattr(element_to_delete,
                                           'image_id'):  # the crud factory is dealing with a link table and needs to look for the Image table item referenced by the link table
            image_id = element_to_delete.image_id
            image_record = session.get(Image, image_id)
            if image_record:
                image_to_delete_from_s3 = image_record
                session.delete(image_record)  # try to delete the image record
        try:
            # todo - should i first check that the image object isn't in use by any other links?
            session.delete(element_to_delete)  # try to delete the link table record
            session.commit()

            # if db commits wre successful, also delete the S3 object to avoid orphaned data in S3
            if image_to_delete_from_s3:
                s3_handler.delete_s3_object(image_to_delete_from_s3.s3_key)

        except Exception:
            session.rollback()
            return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                               message=f"Could not delete {element_type} as it is likely in use.", data=None)

        return ApiResponse(message=f"{element_type} deleted successfully.")

    # conditionally attach an image upload endpoint to the router
    if attach_image_upload_endpoint:
        # Note the dynamic path using the parent's primary key field name
        @router.post(f"/{{{pk_field_name}}}/image/upload", response_model=ApiResponse[None], tags=tags)
        async def image_upload_post(
                # The parent ID is now a path parameter.  DOn't need any form data at this point - can be added later if use wants to PATCH the field to add caption, alt_text etc
                parent_id: int = Path(..., alias=pk_field_name),
                file: UploadFile = File(...),
                # link_data: image_link_model = Depends(parse_image_link_form_data),  # todo - do i need to create a createLinkModel type for this? all link models should be exactly the same type - make all the SQLModel table=true definitions inherit from a generic model file to keep this accurate
                session: Session = Depends(get_session),
                user: User = Depends(get_current_user)
        ):
            # Verify the parent object exists and belongs to the user's org
            parent_obj = session.exec(
                select(model).where(
                    and_(getattr(model, pk_field_name) == parent_id,
                         getattr(model, 'organisation_id') == user.organisation_id)
                )
            ).first()
            if not parent_obj:
                raise ApiResponse(status_code=404, message=f"{element_type} with id {parent_id} not found.", data=None)

            # This assumes a naming convention for the link table and its fields
            # E.g., for Ingredient, it expects Ingredient_Image model and 'ingredient_id' field.
            # A more advanced factory could take these as parameters.
            try:
                # ... (The rest is the same as your original upload logic) ...
                s3_key = s3_handler.push_UploadFile_to_s3(file, directory="image")
                f = pathlib.Path(file.filename)

                image = Image(
                    # ... create image record  todo - create function to extract following elements from file object
                    file_name=f.stem,
                    file_ext=f.suffix,
                    mime_type=file.content_type,
                    file_size=file.size,
                    organisation_id=user.organisation_id,
                    s3_key=s3_key
                )
                session.add(image)
                session.flush()

                link_data = {parent_fk_field: parent_id, "image_id": image.image_id, "organisation_id": user.organisation_id}
                new_link = image_link_model.model_validate(link_data)
                session.add(new_link)
                session.commit()
                return ApiResponse(message="Image linked successfully.")
            except Exception as e:
                session.rollback()
                return ApiResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, message=str(e), data=None)

    return router
