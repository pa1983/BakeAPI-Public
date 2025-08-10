# app/routers/crud_factory.py

from typing import Type, TypeVar, List, Optional, Any


from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError as sqlalchemyIntegrityError
from pymysql.err import IntegrityError as pymlsqlIntegrityError
from sqlmodel import Session, SQLModel, select, and_

from fastapi import APIRouter, Depends, Body, Request
from starlette import status

from app.database.session import get_session
from app.dependencies.user_dependencies import get_current_user
from app.models.common import ApiResponse
from app.models.user import User

# --- Generic Type Variables for strong typing - ensures that all models passed to the factory are SQLModel types---
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)



## original approach - replaced above with function to pull in additional query options for nested querying

def create_crud_router(
        *,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        read_schema: Type[ReadSchemaType],
        update_schema: Type[UpdateSchemaType],
        prefix: str,
        tags: List[str],
        pk_field_name: str = "id",       # The name of the primary key column, defaults to 'id'
        name_field: str = "name",     # A common field for user-friendly messages and log outputs
        get_query_options: Optional[List[Any]] = None , # optionally allow for additional query options, e.g. for nested queries
        filter_by_field: Optional[str] = None  # The field name to optionally filter the /all endpoint
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
        except (sqlalchemyIntegrityError, pymlsqlIntegrityError):
            session.rollback()
            return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                               message=f"{element_type} with that name or identifier already exists.", data=None)
        except Exception as e:
            session.rollback()
            return ApiResponse(status_code=status.HTTP_400_BAD_REQUEST, message=f"Error creating {element_type}: {e}", data=None)

        return ApiResponse(data=read_schema.model_validate(new_element),
                           message=f"{element_type} created successfully.")

    # --- READ ALL (Updated to support optional filtering - initially to allow getting ingredient_buyable linked items from ingredient ID - ) ---
    @router.get("/all", response_model=ApiResponse[List[read_schema]])
    def get_all(
            request: Request, # Added Request to access query params to get filter details, if present
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
            # Check if a value for the filter field was passed in the URL query
            filter_value = request.query_params.get(filter_by_field)
            if filter_value is not None:
                try:
                    # Get the actual column attribute from the model
                    filter_column = getattr(model, filter_by_field)
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



    #
    # # --- READ ALL ---
    # @router.get("/all", response_model=ApiResponse[List[read_schema]])
    # def get_all(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    #     elements = session.exec(
    #         select(model)
    #         .where(getattr(model, 'organisation_id') == user.organisation_id)
    #         .order_by(getattr(model, name_field, None))
    #     ).all()
    #
    #     # Explicitly validate each database object against the read_schema
    #     # This creates a new list of Pydantic models with correctly typed data.
    #     validated_elements = [read_schema.model_validate(el) for el in elements]
    #     # Return the new list of validated Pydantic objects
    #     return ApiResponse(data=validated_elements)
    #
    #
    # # --- READ ONE ---
    # @router.get("/{id}", response_model=ApiResponse[read_schema | None])
    # def get_by_id(id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    #     element = session.exec(
    #         select(model).where(
    #             and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
    #     ).first()
    #
    #     if not element:
    #         return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
    #                            message=f"{element_type} with id {id} not found.", data=None)
    #
    #     return ApiResponse(data=read_schema.model_validate(element))

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

    # --- DELETE ---
    @router.delete("/{id}", response_model=ApiResponse[None])
    def delete_by_id(id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
        element_to_delete = session.exec(
            select(model).where(
                and_(getattr(model, pk_field_name) == id, getattr(model, 'organisation_id') == user.organisation_id))
        ).first()

        if not element_to_delete:
            return ApiResponse(status_code=status.HTTP_404_NOT_FOUND,
                               message=f"{element_type} with id {id} not found.", data=None)
        try:
            session.delete(element_to_delete)
            session.commit()
        except Exception:
            session.rollback()
            return ApiResponse(status_code=status.HTTP_409_CONFLICT,
                               message=f"Could not delete {element_type} as it is likely in use.", data=None)

        return ApiResponse(message=f"{element_type} deleted successfully.")

    return router