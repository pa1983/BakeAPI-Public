from app.api.v1.routers.crud_factory import create_crud_router
from app.models.ingredient_buyable import IngredientBuyable, IngredientBuyableCreate, IngredientBuyableRead, \
    IngredientBuyableUpdate

ingredientBuyableRouter = create_crud_router(
    model = IngredientBuyable,
    create_schema = IngredientBuyableCreate,
    read_schema = IngredientBuyableRead,
    update_schema=IngredientBuyableUpdate,
    prefix="",
    tags=["Ingredient"],
    pk_field_name="id",
    name_field="ingredient_buyable_link",
    filter_by_field="ingredient_id"  # filters the /all endpoint to only return entries for ingredient_id in the all params, i.e. all?ingredient_id=23
)