from __future__ import annotations # Postpone evaluation of type hints to prevent circular import issues
# todo - check all models are imported as per last gemini query

from fastapi import FastAPI
from fastapi_cognito import CognitoAuth
from starlette.middleware.cors import CORSMiddleware
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from app.api.v1.routers.admin import AdminRouter
from app.api.v1.routers.common import CommonRouter, unit_of_measure
from app.api.v1.routers.ingredient import IngredientRouter
from app.core.auth import MyCognitoSettings
from app.dependencies.user_dependencies import get_current_user

from app.models.user import User
from app.models.ingredient_image import Ingredient_Image
from app.models.ingredient import Ingredient
from app.models.uom import unit_of_measure
from app.models.organisation import Organisation
app = FastAPI()
# used to validate and parse data from cognito's JWT
cognito_auth = CognitoAuth(settings=MyCognitoSettings())

app.add_middleware(
    RawContextMiddleware, # used by fastapi-cognito to store and retrieve token info
    plugins=(
        plugins.RequestIdPlugin(),
        plugins.CorrelationIdPlugin()
    )
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

app.include_router(CommonRouter, prefix="/common", tags=["Common"])
app.include_router(AdminRouter, prefix="/admin", tags=["Admin"])
app.include_router(IngredientRouter, prefix="/ingredient", tags=["Ingredient"])
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
