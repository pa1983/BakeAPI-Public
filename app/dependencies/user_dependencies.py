from fastapi import Depends, HTTPException
from fastapi_cognito import CognitoToken
from sqlmodel import Session, select
from starlette import status

from app.core.auth import cognito_auth
from app.database.session import get_session
from app.models.user import User


async def get_current_user(
        session: Session = Depends(get_session),
        cognito_token: CognitoToken = Depends(cognito_auth.auth_required)
) -> User:
    """

    Dependency that gets a SQLModel session, validates cognito token,
    extracts cognito_sub_id and uses this to make a DB query to fetch
    current user's details
    """

    cognito_sub_id: str = cognito_token.cognito_id
    if not cognito_sub_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="cognito sub id not found in Cognito token claims"
        )

    # Query the database to get full user details based on the sub id
    user = session.exec(
        select(User).where(User.cognito_sub_id == cognito_sub_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with Cognito ID '{cognito_sub_id}' not found in User table"
        )

    return user
