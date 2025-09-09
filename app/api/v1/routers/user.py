from fastapi import APIRouter, Depends

from app.dependencies.user_dependencies import get_current_user
from app.models.user import UserReadProfile, UserReadSystem

UserRouter: APIRouter = APIRouter()

@UserRouter.get('/profile', response_model=UserReadProfile)
async def current_user_profile(user: UserReadProfile = Depends(get_current_user)
                                   ) -> UserReadProfile:
    """
    Returns details of currently signed in user.

    :param user: user profile details for display to user; excludes irrelevant system data such as fole_id
    :return:
    """
    return user

@UserRouter.get('/system', response_model=UserReadSystem)
async def current_user_system(user: UserReadSystem = Depends(get_current_user)
                               ) -> UserReadSystem:
    # todo - remove for production - here for testing only
    """
    Returns details of currently signed in user.

    :param user: user profile details for display to user; excludes irrelevant system data such as fole_id
    :return:
    """
    return user