# test_configs.py

from app.models.buyable import BuyableRead
from app.models.brand import BrandRead
from app.models.ingredient import IngredientRead
from app.models.ingredient_buyable import IngredientBuyableRead
from app.models.ingredient_image import Ingredient_ImageRead
from app.models.invoice import LineItemRead
from app.models.labourer import LabourerRead #, LabourCategoryRead
from app.models.recipe import RecipeRead
from app.models.recipe_ingredient import RecipeIngredientRead
from app.models.recipe_labour import RecipeLabourRead
from app.models.recipe_sub_recipe import RecipeSubRecipeRead
from app.models.supplier import SupplierRead

from .CRUDConfig import CRUDConfig

# Existing config for /ingredient
ingredient_config = CRUDConfig(
    endpoint="/ingredient",
    create_payload={
        "ingredient_name": "Sample Ingredient",
        "standard_uom_id": 1,
        "density": 0.6,
        "notes": "Some notes about sample ingredient."
    },
    update_payload={"ingredient_name": "Sample Ingredient - Modified"},
    check_field="ingredient_name",
    pk_field="ingredient_id",
    response_model=IngredientRead,
)

# Config for /ingredient/link_buyable
ingredient_buyable_config = CRUDConfig(
    endpoint="/ingredient/link_buyable",
    create_payload={
        "ingredient_id": 1,
        "buyable_id": 1,
        "sort_order": 10,
        "notes": "Link ingredient to buyable."
    },
    update_payload={"notes": "Link ingredient to buyable - Modified"},
    check_field="notes",
    pk_field="id",
    response_model=IngredientBuyableRead,
)

# Config for /ingredient_image
# NOTE: The Create schema for this endpoint does not include `ingredient_id`, which may be injected by the API logic.
# The check_field is 'sort_order' as it's the main updatable, non-key field.
ingredient_image_config = CRUDConfig(
    endpoint="/ingredient_image",
    create_payload={
        "image_id": 1,
        "sort_order": 10
    },
    update_payload={"sort_order": 20},
    check_field="sort_order",
    pk_field="id",
    response_model=Ingredient_ImageRead,
)

# Config for /invoice/lineitem
line_item_config = CRUDConfig(
    endpoint="/invoice/lineitem",
    create_payload={
        "invoice_id": 1,
        "description": "Test Line Item",
        "value_ex_vat": 100.0,
        "vat_percentage": 20.0
    },
    update_payload={"description": "Test Line Item - Modified"},
    check_field="description",
    pk_field="id",
    response_model=LineItemRead,
)

# Config for /buyable
buyable_config = CRUDConfig(
    endpoint="/buyable",
    create_payload={
        "brand_id": 1,
        "sku": "TST-001",
        "item_name": "Test Buyable Item",
        "uom_id": 1,
        "quantity": "1.0"
    },
    update_payload={"item_name": "Test Buyable Item - Modified"},
    check_field="item_name",
    pk_field="id",
    response_model=BuyableRead,
)

# Config for /buyable/brand
brand_config = CRUDConfig(
    endpoint="/buyable/brand",
    create_payload={
        "brand_name": "Test Brand",
        "notes": "Notes for test brand."
    },
    update_payload={"brand_name": "Test Brand - Modified"},
    check_field="brand_name",
    pk_field="brand_id",
    response_model=BrandRead,
)

# Config for /buyable/supplier
supplier_config = CRUDConfig(
    endpoint="/buyable/supplier",
    create_payload={
        "supplier_name": "Test Supplier Ltd",
        "currency_code": "GBP",
        "notes": "A test supplier."
    },
    update_payload={"supplier_name": "Test Supplier Ltd - Modified"},
    check_field="supplier_name",
    pk_field="supplier_id",
    response_model=SupplierRead,
)

# Config for /recipe
recipe_config = CRUDConfig(
    endpoint="/recipe",
    create_payload={
        "recipe_name": "Test Recipe",
        "recipe_description": "A delicious test recipe.",
        "recipe_type_id": 1,
        "product_type_id": 1,
        "recipe_status_id": 1,
        "recipe_uom_id": 1,
        "recipe_quantity": "500.0"
    },
    update_payload={"recipe_name": "Test Recipe - Modified"},
    check_field="recipe_name",
    pk_field="recipe_id",
    response_model=RecipeRead,
)

# Config for /recipe_ingredient
recipe_ingredient_config = CRUDConfig(
    endpoint="/recipe_ingredient",
    create_payload={
        "recipe_id": 1,
        "ingredient_id": 1,
        "quantity": "100.0",
        "uom_id": 2,
        "notes": "Add test ingredient to recipe."
    },
    update_payload={"notes": "Add test ingredient to recipe - Modified"},
    check_field="notes",
    pk_field="id",
    response_model=RecipeIngredientRead,
)

# Config for /labourer
labourer_config = CRUDConfig(
    endpoint="/labourer",
    create_payload={
        "name": "Test Labourer",
        "description": "A worker for testing."
    },
    update_payload={"name": "Test Labourer - Modified"},
    check_field="name",
    pk_field="id",
    response_model=LabourerRead,
)


# Config for /recipe_labour
recipe_labour_config = CRUDConfig(
    endpoint="/recipe_labour",
    create_payload={
        "recipe_id": 1,
        "labourer_id": 1,
        "labour_minutes": "30.0",
        "labour_category_id": 1,
        "description": "Initial mixing phase."
    },
    update_payload={"description": "Initial mixing phase - Modified"},
    check_field="description",
    pk_field="id",
    response_model=RecipeLabourRead,
)

# Config for /recipe_sub_recipe
recipe_sub_recipe_config = CRUDConfig(
    endpoint="/recipe_sub_recipe",
    create_payload={
        "parent_recipe_id": 1,
        "sub_recipe_id": 2,
        "quantity": "1.0",
        "uom_id": 5,
        "notes": "Add sub-recipe to parent.",
        "sort_order": 10
    },
    update_payload={"notes": "Add sub-recipe to parent - Modified"},
    check_field="notes",
    pk_field="id",
    response_model=RecipeSubRecipeRead,
)


# Combine all configs into a single list for the test runner
all_crud_configs = [
    ingredient_config,
    ingredient_buyable_config,
    # ingredient_image_config, # Potentially problematic, enable with caution.
    line_item_config,
    buyable_config,
    brand_config,
    supplier_config,
    recipe_config,
    recipe_ingredient_config,
    labourer_config,
    recipe_labour_config,
    recipe_sub_recipe_config,
]