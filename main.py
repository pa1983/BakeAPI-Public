from __future__ import annotations  # Postpone evaluation of type hints to prevent circular import issues
# todo - check all models are imported as per last gemini query

from fastapi import FastAPI, Depends, Request
from app import models  #  import all model files up front to avoid circular dependancy errors
from fastapi_pagination import add_pagination
from fastapi.security import OAuth2PasswordBearer
from fastapi_cognito import CognitoAuth, CognitoToken
from starlette.middleware.cors import CORSMiddleware
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from app.api.v1.routers.invoice import InvoiceRouter
from app.api.v1.routers.buyable import buyableRouter
from app.api.v1.routers.labourer import labourerRouter
from app.api.v1.routers.recipe import recipeRouter
from app.api.v1.routers.recipe_ingredient import recipeIngredientRouter
from app.api.v1.routers.recipe_labour import recipeLabourRouter
from app.api.v1.routers.recipe_sub_recipe import recipeSubRecipe
from app.core.logging_config import logger
from app.api.v1.routers.common import CommonRouter
from app.api.v1.routers.ingredient import IngredientRouter, IngredientImageRouter
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
    allow_origins=["http://localhost:5174",
                   "https://bake.ardmillan.ie",
                   "https://api.ardmillan.ie",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# todo - go through all routers and remove instances where full error is passed back to user in the api response - convert to something user-friendly and log the error, poss with a unique error id for tracking?
# find by searching for all message= and remove and error/e instances

app.include_router(CommonRouter, prefix="/common", tags=["Common"])
app.include_router(IngredientRouter, prefix="/ingredient", tags=["Ingredient"])
app.include_router(IngredientImageRouter, prefix="/ingredient_image", tags=["Ingredient Image"])
app.include_router(UserRouter, prefix="/user", tags=["User"])
app.include_router(InvoiceRouter, prefix="/invoice", tags=["Invoice"])
app.include_router(buyableRouter, prefix="/buyable", tags=["Buyable"])
app.include_router(recipeRouter, prefix="/recipe", tags=["Recipe"])
app.include_router(recipeIngredientRouter, prefix="/recipe_ingredient", tags=["Recipe Ingredient"])
# instantiate pagination - must comme after all routers are declared
app.include_router(labourerRouter, prefix="/labourer", tags=["Labourer"])

app.include_router(recipeLabourRouter, prefix="/recipe_labour", tags=["Recipe Labour"])

app.include_router(recipeSubRecipe, prefix="/recipe_sub_recipe", tags=["Recipe Sub Recipe"])


@app.get("/debug-headers")
async def debug_headers(request: Request):
    # This will print to your Docker container's logs
    print(f"DEBUG: Incoming request headers: {request.headers}")
    # This will return the headers as a JSON response
    return {"headers": dict(request.headers)}

add_pagination(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
