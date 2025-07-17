from __future__ import annotations  # Postpone evaluation of type hints to prevent circular import issues
# todo - check all models are imported as per last gemini query

from fastapi import FastAPI, Depends
from fastapi_pagination import add_pagination
from fastapi.security import OAuth2PasswordBearer
from fastapi_cognito import CognitoAuth, CognitoToken
from starlette.middleware.cors import CORSMiddleware
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from app.api.v1.routers.invoice import InvoiceRouter
from app.core.logging_config import logger
from app.api.v1.routers.admin import AdminRouter
from app.api.v1.routers.common import CommonRouter
from app.api.v1.routers.ingredient import IngredientRouter
from app.api.v1.routers.user import UserRouter
from app.core.auth import MyCognitoSettings, cognito_auth
from app.dependencies.user_dependencies import get_current_user

from app.models.user import User
from app.models.ingredient_image import Ingredient_Image
from app.models.ingredient import Ingredient
from app.models.uom import UnitOfMeasure
from app.models.organisation import Organisation

app = FastAPI(title="BakeAPI")

# app.security_schemes = {
#     "BearerAuth": {
#         "type": "http",
#         "scheme": "bearer",
#         "bearerFormat": "JWT",
#         "description": "Enter your Cognito JWT (Access Token or ID Token) in the format 'Bearer <token>'"
#     }
# }

# app.add_middleware(
#     RawContextMiddleware,  # used by fastapi-cognito to store and retrieve token info
#     plugins=(
#         plugins.RequestIdPlugin(),
#         plugins.CorrelationIdPlugin()
#     )
# )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



app.include_router(CommonRouter, prefix="/common", tags=["Common"])
app.include_router(AdminRouter, prefix="/admin", tags=["Admin"])
app.include_router(IngredientRouter, prefix="/ingredient", tags=["Ingredient"])
app.include_router(UserRouter, prefix="/user", tags=["User"])
app.include_router(InvoiceRouter, prefix="/invoice", tags=["Invoice"])

# instantiate pagination - must comme after all routers are declared
add_pagination(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/protected-route-example", tags=["Protected"])
async def protected_example(auth: CognitoToken = Depends(cognito_auth.auth_required)):
    """
    An example of a protected route requiring a Cognito token.
    The 'Authorize' button will appear in the docs because of this dependency.
    """
    return {"message": f"You are authenticated, {auth.username}! Your email is {auth.cognito_id}"}
