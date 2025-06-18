from fastapi import APIRouter, Depends

from app.dependencies.user_dependencies import get_current_user
from app.models.user import UserReadProfile

AdminRouter: APIRouter = APIRouter()

# todo - create:
# modify user role
# modify role-permission (list of check boxes per role)

# look up permissions by user.  Users might be able to VIEW this, but not modify.
# Admin will have both get and post access
# what does this look like in sql model?  need custom response type to merge multiple tables?


@AdminRouter.get('/user/{cognito_sub_id}', response_model=UserReadProfile)
async def admin_get_user_by_sub_id(cognito_sub_id: str,
                                   user: UserReadProfile = Depends(get_current_user)
                                   ) -> UserReadProfile:
    """
    Returns details of a user from their sub ID.  Used for admin and testing purposes
    # todo - lock this down for admin access only for production
    :param cognito_sub_id:
    :return:
    """
    return user

