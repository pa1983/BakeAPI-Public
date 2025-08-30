from fastapi import Depends, HTTPException, Request
from fastapi_cognito import CognitoToken
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from starlette import status

from app.core.logging_config import logger
from app.database.session import get_session
from app.models.role import Role
from app.models.user import User, UserReadProfile, UserReadSystem
from app.core.auth import cognito_auth


async def get_current_user(
        request: Request,
        session: Session = Depends(get_session)
) -> UserReadProfile:
    """

    Dependency that gets a SQLModel session, validates cognito token using the cognito_auth package,
    extracts cognito_sub_id and uses this to make a DB query to fetch a full object of the
    current user's details from the database

    """
    # todo - later, implement RBAC using:
    # if current_user.role and any(p.name == "add_ingredient" for p in current_user.role.permissions):
    try:
        cognito_token: CognitoToken = await cognito_auth.auth_required(request=request)
        if cognito_token:
            cognito_sub_id: str = cognito_token.cognito_id
            if not cognito_sub_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="cognito sub id not found in Cognito token claims"
                )
        else:
            cognito_sub_id: str = 'd2e5a494-2061-7025-bc08-2c55e8066af6'
            print("Warning - SECURITY NOT ENABLED - USING DEFAULT TEST COGNITO ID TO BYPASS SECURITY DURING TESTING")
        # Query the database to get full user details based on the sub id;
        # used nested eager loading to pull permissions as sub-queries (selectinload)
        user = session.exec(select(User)
                            .where(User.cognito_sub_id == cognito_sub_id)
                            .options(selectinload(User.organisation),
                                     selectinload(User.role).selectinload(Role.permissions)
                                     ))
        res = user.first()
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with Cognito ID '{cognito_sub_id}' not found in User table"
            )
        usr = UserReadSystem.model_validate(res)
        return usr
    except Exception as e:
        print(e)
        logger.exception(e)
        raise HTTPException(status_code=401, detail=f"Error getting or validating current user. See logs.")
