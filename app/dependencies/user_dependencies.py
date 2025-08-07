from fastapi import Depends, HTTPException, Request
from fastapi_cognito import CognitoToken
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from starlette import status

from app.core.logging_config import logger
from app.database.session import get_session
from app.models.role import Role
from app.models.role_permission_link import RolePermissionLink
from app.models.user import User, UserReadProfile, UserReadSystem
from app.core.auth import cognito_auth
# from main import cognito_auth

# async def get_current_user(
#         request: Request,
#         session: Session = Depends(get_session)
#         ,cognito_token: CognitoToken = Depends(cognito_auth.auth_required)
# ) -> UserReadProfile:
#     """
#
#     Dependency that gets a SQLModel session, validates cognito token,
#     extracts cognito_sub_id and uses this to make a DB query to fetch
#     current user's details
#
#     sample cognito token:
#     CognitoToken(origin_jti='9eee907d-660a-4e08-aa0c-4f722cf07ae0', cognito_id='d2e5a494-2061-7025-bc08-2c55e8066af6',
#     event_id='cc506764-57de-4464-b148-623b957f98d6', token_use='access', scope='aws.cognito.signin.user.admin',
#     auth_time=1750164289, iss=HttpUrl('https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_l4pSAAZYP'),
#     exp=1750167889, iat=1750164289, jti='c7e2d217-b1a2-42e1-ac47-4cbd1d5cc39a',
#     client_id='4ph7lbuua09u9qstvlc6mf2i4', username='d2e5a494-2061-7025-bc08-2c55e8066af6')
#     """
#     # todo - later, implement RBAC using:
#     # if current_user.role and any(p.name == "add_ingredient" for p in current_user.role.permissions):
#
#     if request.method == "OPTIONS":
#          # // added to try and resolve cors-related error that was allowing options requests to find their way to this dependancy and fail when no auth was present
#         logger.info("An OPTIONS request found its way to the get_current_user dependancy");
#         pass
#
#     try:
#         # todo - come back and tidy this up once get system running.  Not currnetly handling the cognito id from cookies
#         if cognito_token:
#
#             cognito_sub_id: str = cognito_token.cognito_id
#             if not cognito_sub_id:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="cognito sub id not found in Cognito token claims"
#                 )
#
#         else:
#             cognito_sub_id: str = 'd2e5a494-2061-7025-bc08-2c55e8066af6'
#             print("Warning - SECURITY NOT ENABLED - USING DEFAULT TEST COGNITO ID TO BYPASS SECURITY DURING TESTING")
#         # Query the database to get full user details based on the sub id;
#         # used nested eager loading to pull permissions as sub-queries (selectinload)
#         user = session.exec(select(User)
#                             .where(User.cognito_sub_id == cognito_sub_id)
#                             .options(selectinload(User.organisation),
#                                      selectinload(User.role).selectinload(Role.permissions)
#                                      ))
#
#         res = user.first()
#
#         if not res:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"User with Cognito ID '{cognito_sub_id}' not found in User table"
#             )
#
#         usr = UserReadSystem.model_validate(res)
#         print(f'available user permissions: {usr.role.permissions}')
#
#         return usr
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"{e.args}")


async def get_current_user(
        request: Request,
        session: Session = Depends(get_session)
) -> UserReadProfile:
    """

    Dependency that gets a SQLModel session, validates cognito token,
    extracts cognito_sub_id and uses this to make a DB query to fetch
    current user's details

    sample cognito token:
    CognitoToken(origin_jti='9eee907d-660a-4e08-aa0c-4f722cf07ae0', cognito_id='d2e5a494-2061-7025-bc08-2c55e8066af6',
    event_id='cc506764-57de-4464-b148-623b957f98d6', token_use='access', scope='aws.cognito.signin.user.admin',
    auth_time=1750164289, iss=HttpUrl('https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_l4pSAAZYP'),
    exp=1750167889, iat=1750164289, jti='c7e2d217-b1a2-42e1-ac47-4cbd1d5cc39a',
    client_id='4ph7lbuua09u9qstvlc6mf2i4', username='d2e5a494-2061-7025-bc08-2c55e8066af6')
    """
    # todo - later, implement RBAC using:
    # if current_user.role and any(p.name == "add_ingredient" for p in current_user.role.permissions):

    # if request.method == "OPTIONS":
    #      # // added to try and resolve cors-related error that was allowing options requests to find their way to this dependancy and fail when no auth was present
    #     logger.info("An OPTIONS request found its way to the get_current_user dependancy");
    #     return User(cognito_sub_id="asd123", username="Dummy", email="Dummy@dummy.com")

    try:
        # todo - come back and tidy this up once get system running.  Not currnetly handling the cognito id from cookies
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
        # print(f'available user permissions: {usr.role.permissions}')

        return usr
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail=f"{e} - {e.args}")
