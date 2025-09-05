# app/routers/crud_factory.py

from typing import Type, TypeVar, List, Optional, Any
import pathlib

from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, SQLModel, select, and_

from fastapi import APIRouter, Depends, Body, Request, File, UploadFile, Path, Form, HTTPException
from starlette import status
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY

from app.core.logging_config import logger
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
        logger.exception(e)
        raise HTTPException(detail="Error validating form data", status_code=HTTP_400_BAD_REQUEST)


def create_crud_router(
        *,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        read_schema: Type[ReadSchemaType],
        update_schema: Type[UpdateSchemaType],
        prefix: Optional[str] = "",
        # keep here for future flexibility, but mostly prefer to define prefix when
        # using the router in main to make it easier to see in an overview where all the routers point to
        tags: List[str] = [],
        pk_field_name: str = "id",  # The name of the primary key column, defaults to 'id'
        name_field: str = "name",  # A common field for user-friendly messages and log outputs
        get_query_options: Optional[List[Any]] = None,
        # optionally allow for additional query options, e.g. for nested queries
        filter_by_field: Optional[str] = None,  # The field name to optionally filter the /all endpoint,
        image_link_model: Optional[Type[ModelType]] = None,
        # if endpoint requires the option to upload images for the parent model,
        # include an image link model to conditionally add delete all image links,
        # images, and s3 objects when deleting the element
        parent_fk_field: Optional[str] = None,
        # required if passing an image link model so it knows what the field
        # name of parent is to link to (image pk name always the same)
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
    @router.post("", response_model=ApiResponse[read_schema | None],
                 status_code=status.HTTP_201_CREATED,
                 summary=f"Create a new {element_type}",
                 description=f"""Create a new {element_type} in the database using schema *{create_schema}* 
                 and return the new {element_type} as a JSON object with primary key name {pk_field_name}""",
                 tags=tags)
    def create_new(
            form_data: create_schema = Body(...),
            session: Session = Depends(get_session),
            user: User = Depends(get_current_user)
    ):
        try:
            # broken down into steps to debug
            validated_data = form_data.model_dump()
            # Get the user's org_id from the user dependency and add it to the validated_data
            validated_data['organisation_id'] = user.organisation_id
            new_element = model.model_validate(validated_data)
            session.add(new_element)
            session.commit()
            session.refresh(new_element)
        except (sqlalchemyIntegrityError, pymlsqlIntegrityError) as e:
            session.rollback()
            # No logging as this isn't a server error, just a user error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{element_type} with that name or identifier already exists, or a foreign key does not exist.")

        except Exception as e:
            session.rollback()
            print(e, e.args)
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating {element_type}")

        return ApiResponse(data=read_schema.model_validate(new_element),
                           message=f"{element_type} created successfully.")

    # --- READ ALL (Updated to support optional filtering - initially to allow getting ingredient_buyable linked items from ingredient ID - ) ---
    @router.get("/all",
                response_model=ApiResponse[List[read_schema]],
                summary=f"Get a list of all {element_type}s",
                description=f"""Get a list of all {element_type}s in the database using schema *{read_schema}*.
                            Primary key field name is {pk_field_name}.""",
                tags=tags
                )
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

        #  APPLY THE DYNAMIC FILTER, IF  PROVIDED
        if filter_by_field:
            print(f'filtering by {filter_by_field}')
            # Check if a value for the filter field was passed in the URL query
            filter_value = request.query_params.get(
                filter_by_field)  # check the params for a query fieldname matching the filter_by_field passed in.
            #  If this doesn't match, all results will be returned
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

        elements = session.exec(statement).all()
        validated_elements = [read_schema.model_validate(el) for el in elements]
        return ApiResponse(data=validated_elements)

    @router.get("/{id}",
                response_model=ApiResponse[read_schema | None],
                summary=f"Get a single {element_type}",
                description=f"""Get a single {element_type} by its primary key id (field name *{pk_field_name}*)
                in the database using schema *{read_schema}*""",
                tags=tags)
    def get_by_id(id: int,
                  session: Session = Depends(get_session),
                  user: User = Depends(get_current_user)):
        statement = select(model).where(
            and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id)
        )


        if get_query_options:
            statement = statement.options(*get_query_options)

        element = session.exec(statement).first()

        if not element:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"{element_type} with id {id} not found.")

        return ApiResponse(data=read_schema.model_validate(element))


    # the router watches for a PATCH operation on the base path and calls the update_partial method,
    # making the {id} parameter available to the method.
    @router.patch("/{id}",
                  # declaring the response_model here adds it to the openapi documentation; The model is an
                  # ApiResponse object with the read_schema defined as the data field.
                  response_model=ApiResponse[read_schema | None],
                  # The default status code for a successful PATCH operation.  204 No Content is often used for
                  # PATCH responses, but it was decided to use 200 OK because the full updated object is being
                  # returned in the response body so that it can be used to update local state in the frontend client.
                  status_code=status.HTTP_200_OK,
                  # The summary and description are used in the openapi documentation.  The description makes use of
                  # markup notation to make the documentation more user-friendly and lists all fields that can be
                  # updated as a developer convenience.
                  summary=f"Update one or more field of {element_type}",
                  description=f"""Update a {element_type} by its primary key id (field name *{pk_field_name}*)
                    in the database using schema *{update_schema}*. 
                    Updatable fields are: {[fieldname for fieldname in update_schema.model_fields]}""",
                  tags=tags)
    def update_partial(
            # id - passed in by the router decorator
            id: int,
            # update_data is taken from the Body of the request, is typed with the update_schema type defined in the
            # create_crud_router's signature. FastAPI will automatically parse the request body into this type
            update_data: update_schema = Body(...),
            # The session provided by the Depends() is used to access the database
            session: Session = Depends(get_session),
            # get_current_user dependency validated the user's Bearer token and makes the User object available to the method
            user: User = Depends(get_current_user)
    ):
        # First get the element to update from the database using the id and user's organisation_id (this is the multi-tenancy protection)
        element_to_update = session.exec(
            select(model).where(
                and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
        ).first()
        # If an element isn't found, return a 404 error message and stop processing.
        # HTTPException is a standard exception class in FastAPI that can be raised to directly return an error response to the client.
        if not element_to_update:
            # the logger.error() method is used to log an error message using parameters from the parent function's definition,
            # including the element's tye and ID.
            logger.error(f"Partial Update failed - {element_type} with id {id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"{element_type} with id {id} not found.")

        # This step checks that the update data passed from the front end to the API complies with the update_data schema_requirements
        # If a request attempts to patch a field that doesn't exist in the update_data schema, it will be silently excluded from the update_dict and ignored.
        update_dict = update_data.model_dump(exclude_unset=True)
        # If the update_dict is empty, return a 400 error message and stop processing. This may happen even if the
        # update body were not empty if the fields provided weren't present in the update_data schema.
        if not update_dict:
            logger.error("No update data provided to update_partial - update_dict is empty.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="No update data provided.")

        # At this point it can be assumed that the data in update_dict is safe; so we iterate through the keys and values from the dictionary
        # and update the corresponding attribute on the element_to_update object.
        for key, value in update_dict.items():
            setattr(element_to_update, key, value)

        try:
            # The updated element is then added and commited to the database
            session.add(element_to_update)
            session.commit()
            # The updated element is then refreshed to ensure that the database has updated the values.
            # This ensures that the returned object is up-to-date with the database.
            session.refresh(element_to_update)
        except (sqlalchemyIntegrityError, pymlsqlIntegrityError) as e:
            # If a database integrity error is thrown during the commit it indicates that the provided ID doesn't exist
            # or that the data provided for a field doesn't match the database constraints.
            session.rollback()
            # log the full details error message using the logger.exception() method.
            logger.exception(f"Partial Update failed - {element_type} with id {id} already exists or datatype doesn't match constraints {e}")
            # raise an HTTPException to return a 409 Conflict error message to the client, with a descriptive error message.
            # Note that the full exception details in e are NOT included as this risks leaking sensitive information
            # and database/API structural information that could be used by a potential attacker.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Update failed. A {element_type} with that name may already exist or the data type doesn't match constraints.")
        # If this point is reached, the update was successful and the element_to_update object has been updated with the new data.
        # The element to update is used to set a read_schema object and returned to the client.  This is used rather than returning the full
        # model object to avoid returning sensitive information that should not be exposed to the client.
        return ApiResponse(data=read_schema.model_validate(element_to_update),
                           message=f"{element_type} updated successfully.")

    # --- DELETE
    # ## conditionally checks for image_link_model to see if it also needs to remove matching image elements  ---
    # in hindsight this should default to status 204, but would break usages in front end that expect an ApiResponse with a message to flash
    @router.delete("/{id}",
                   response_model=ApiResponse[None],
                   status_code=status.HTTP_200_OK,
                   summary=f"Delete one {element_type}",
                   description=f"""Delete a {element_type} by its primary key id (field name *{pk_field_name}*)""",
                   tags=tags)

    def delete_by_id(id: int,
                     session: Session = Depends(get_session),
                     user: User = Depends(get_current_user)):
        element_to_delete = session.exec(
            select(model).where(
                and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
        ).first()

        if not element_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"{element_type} with id {id} not found.")

        image_to_delete_from_s3 = None
        if is_image_link_model and hasattr(element_to_delete,
                                           'image_id'):
            # the crud factory is dealing with a link table and needs to look for the Image table item referenced by the link table
            image_id = element_to_delete.image_id
            image_record = session.get(Image, image_id)
            if image_record:
                image_to_delete_from_s3 = image_record
                session.delete(image_record)  # try to delete the image record
        try:
            # todo - should i first check that the image object isn't in use by any other links?
            session.delete(element_to_delete)  # try to delete the link table record
            session.commit()

            # if db commits were successful, also delete the S3 object to avoid orphaned data in S3
            if image_to_delete_from_s3:
                s3_handler.delete_s3_object(image_to_delete_from_s3.s3_key)

        except Exception:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Could not delete {element_type} as it is likely in use.")

        return ApiResponse(message=f"{element_type} deleted successfully.")

    # conditionally attach an image upload endpoint to the router
    if attach_image_upload_endpoint:
        # Note the dynamic path using the parent's primary key field name
        @router.post(f"/{pk_field_name}/image/upload",
                     response_model=ApiResponse[None],
                     status_code=status.HTTP_201_CREATED,
                     summary=f"Upload an image to {element_type}",
                     tags=tags)
        async def image_upload_post(
                # The parent ID is now a path parameter.  Don't need any form data at this point -
                # can be added later if use wants to PATCH the field to add caption, alt_text etc
                parent_id: int = Path(..., alias=pk_field_name),
                file: UploadFile = File(...),
                # link_data: image_link_model = Depends(parse_image_link_form_data),  # todo - do i need to create a createLinkModel type for this? all link models should be exactly the same type - make all the SQLModel table=true definitions inherit from a generic model file to keep this accurate
                session: Session = Depends(get_session),
                user: User = Depends(get_current_user)
        ):
            # Verify the parent object exists and belongs to the user's organisation
            parent_obj = session.exec(
                select(model).where(
                    and_(getattr(model, pk_field_name) == parent_id,
                         getattr(model, 'organisation_id') == user.organisation_id)
                )
            ).first()
            if not parent_obj:
                raise HTTPException(status_code=404,
                                    detail=f"{element_type} with id {parent_id} not found.")

            # This assumes a naming convention for the link table and its fields
            # E.g., for Ingredient, it expects Ingredient_Image model and 'ingredient_id' field.
            try:
                # push the file to S3 and get the S3 key
                s3_key = s3_handler.push_UploadFile_to_s3(file, directory="image")
                # Use pathlib to parse the filename details - these are broken down in the image model to allow
                # for filtering, sorting etc later
                f = pathlib.Path(file.filename)

                image = Image(
                    file_name=f.stem,
                    file_ext=f.suffix,
                    mime_type=file.content_type,
                    file_size=file.size,
                    organisation_id=user.organisation_id,
                    s3_key=s3_key
                )
                session.add(image)
                session.flush()
                # An entry is created in the appropriate link table to link the image to the parent object
                link_data = {parent_fk_field: parent_id,
                             "image_id": image.image_id,
                             "organisation_id": user.organisation_id}
                new_link = image_link_model.model_validate(link_data)
                session.add(new_link)
                session.commit()
                return ApiResponse(message="Image linked successfully.")
            except Exception as e:
                session.rollback()
                logger.exception(f'error in crud factory image upload: {e}')
                raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Error uploading image. Please try again.")

    return router
