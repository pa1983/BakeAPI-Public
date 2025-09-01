"""
Crud test suit for use in testing of join tables, e.g. recipe_ingredient - the test needs a recipe and ingredient
created in the DB before it can test the creation of the join
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.dependencies.user_dependencies import get_current_user
from app.models import RecipeIngredientRead
from app.models.buyable import BuyableRead
from app.models.common import ApiResponse
from app.models.ingredient import IngredientRead
from app.models.ingredient_buyable import IngredientBuyableRead
from app.models.invoice import InvoiceRead, LineItemRead
from app.models.labourer import LabourerRead
from app.models.recipe import RecipeRead
from app.models.recipe_labour import RecipeLabourRead
from app.models.recipe_sub_recipe import RecipeSubRecipeRead
from main import app
from .test_configs import recipe_labour_config, ingredient_config, buyable_config, recipe_config, \
    ingredient_buyable_config, recipe_ingredient_config, labourer_config, recipe_sub_recipe_config
from .CRUDConfig import override_get_current_user
### Fixtures required by linked table crud tests - each link tables needs either side of the link created before
### the linking test can run.  Each fixture creates the instance, yields it for testing, then deletes it after the test
# returns
# todo - test image uploads - a little different to other tests so far as the image is sent to the ingredient endpoint, saved, then the link created without any need for awareness of the ID of the image DB entry

from faker import Faker

app.dependency_overrides[get_current_user] = override_get_current_user

fake = Faker()

@pytest.fixture
def created_ingredient(client: TestClient):
    """Fixture to create a single Ingredient for prerequisite testing."""
    # Create a unique payload for each run
    payload = ingredient_config.create_payload.copy()
    unique_name = f"Test Ingredient {fake.word()} {datetime.now().isoformat()}"
    payload['ingredient_name'] = unique_name

    print(f"SETUP: Creating ingredient '{unique_name}'")
    response = client.post(ingredient_config.endpoint, json=payload)
    if response.status_code != 201:
        print(f"ERROR in created_ingredient fixture: {response.json()}")
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    ingredient = ingredient_config.response_model.model_validate(res.data)

    yield ingredient

    print(f"TEARDOWN: Deleting ingredient {ingredient.ingredient_id}")
    client.delete(f'{ingredient_config.endpoint}/{ingredient.ingredient_id}')

@pytest.fixture
def created_buyable(client: TestClient):
    """Fixture to create a Buyable item with a unique name for each test run."""
    payload = buyable_config.create_payload.copy()
    # Assuming the unique field is 'buyable_name'. Adjust if necessary.
    unique_name = f"Test Buyable {fake.company()} {datetime.now().isoformat()}"
    payload['buyable_name'] = unique_name
    payload['sku'] = f"SKU-{fake.name()} {datetime.now().isoformat()}"

    print(f"SETUP: Creating buyable '{unique_name}'")
    response = client.post(buyable_config.endpoint, json=payload)

    if response.status_code != 201:
        print(f"ERROR in created_buyable fixture: {response.json()}")
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    buyable = buyable_config.response_model.model_validate(res.data)

    yield buyable

    print(f"TEARDOWN: Deleting buyable {buyable.id} ('{unique_name}')")
    client.delete(f'{buyable_config.endpoint}/{buyable.id}')
    print("Buyable torn down")

@pytest.fixture
def created_recipe(client: TestClient):
    """Fixture to create a Recipe with a unique name for each test run."""
    payload = recipe_config.create_payload.copy()
    # Assuming the unique field is 'recipe_name'. Adjust if necessary.
    unique_name = f"Test Recipe {fake.bs()} {datetime.now().isoformat()}"
    payload['recipe_name'] = unique_name

    print(f"SETUP: Creating recipe '{unique_name}'")
    response = client.post(recipe_config.endpoint, json=payload)

    if response.status_code != 201:
        print(f"ERROR in created_recipe fixture: {response.json()}")
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    recipe = recipe_config.response_model.model_validate(res.data)

    yield recipe

    print(f"TEARDOWN: Deleting recipe {recipe.recipe_id} ('{unique_name}')")
    client.delete(f'{recipe_config.endpoint}/{recipe.recipe_id}')



@pytest.fixture
def created_recipe_labour_link(
        client: TestClient,
        created_recipe: RecipeRead,
        created_labour: LabourerRead
) -> RecipeLabourRead:
    """
    Fixture to create a complete recipe-labour link.
    It depends on the recipe and labour fixtures and handles its own cleanup.
    """
    # SETUP: Create the link using fields from the RecipeLabourCreate schema
    payload = {
        "recipe_id": created_recipe.recipe_id,
        "labourer_id": created_labour.id,
        "labour_minutes": 15,
        "labour_category_id": 1,  # Assuming 1 is a valid category ID
        "description": "Initial fixture labour step."
    }

    response = client.post(recipe_labour_config.endpoint, json=payload)
    assert response.status_code == 201
    res = ApiResponse.model_validate(response.json())
    link_object = RecipeLabourRead.model_validate(res.data)

    yield link_object  # The test runs here

    # TEARDOWN: This guaranteed cleanup is key to robust tests
    print(f"TEARDOWN: Deleting recipe_labour link {link_object.id}")
    client.delete(f'{recipe_labour_config.endpoint}/{link_object.id}')



@pytest.fixture
def created_ingredient_buyable_link(
        client: TestClient,
        created_ingredient: IngredientRead,
        created_buyable: BuyableRead
) -> IngredientBuyableRead:
    """
    Fixture to create a complete ingredient-buyable link.
    It depends on the ingredient and buyable fixtures and handles its own cleanup.
    Used by the ingredient_buyable_CRUD_test.py for parts R, U & D
    """

    payload = ingredient_buyable_config.create_payload.copy()
    payload["ingredient_id"] = created_ingredient.ingredient_id
    payload["buyable_id"] = created_buyable.id

    response = client.post(ingredient_buyable_config.endpoint, json=payload)
    assert response.status_code == 201
    res = ApiResponse.model_validate(response.json())
    link_object = IngredientBuyableRead.model_validate(res.data)

    yield link_object # The test runs here

    # TEARDOWN: Delete the link. This will ALWAYS run after the yield - resolves the problem if the test fails where was getting orphaned data blocking subsequent tests
    print(f"TEARDOWN: Deleting ingredient_buyable link {link_object.id}")
    client.delete(f'{ingredient_buyable_config.endpoint}/{link_object.id}')


@pytest.fixture
def created_recipe_ingredient_link(
        client: TestClient,
        created_recipe: RecipeRead,
        created_ingredient: IngredientRead
) -> RecipeIngredientRead:
    """
    Fixture to create a complete recipe-ingredient link.
    It depends on the recipe and ingredient fixtures and handles its own cleanup.
    """
    payload = {
        "recipe_id": created_recipe.recipe_id,
        "ingredient_id": created_ingredient.ingredient_id,
        "quantity": 100.5,
        "uom_id": 1,
        "notes": "Initial test note for recipe ingredient link."
    }

    response = client.post(recipe_ingredient_config.endpoint, json=payload)
    assert response.status_code == 201
    res = ApiResponse.model_validate(response.json())
    link_object = RecipeIngredientRead.model_validate(res.data)

    yield link_object  # The test runs here

    # TEARDOWN: This guaranteed cleanup is the key to robust tests
    print(f"TEARDOWN: Deleting recipe_ingredient link {link_object.id}")
    client.delete(f'{recipe_ingredient_config.endpoint}/{link_object.id}')


@pytest.fixture
def created_labour(client: TestClient) -> LabourerRead:
    """Fixture to create a Labourer with a unique name for each test run."""
    payload = labourer_config.create_payload.copy()

    unique_name = f"Tst Labourer {fake.job()} {datetime.now().isoformat()}"[:49]  # max length 50 cahrs
    payload['name'] = unique_name

    print(f"SETUP: Creating labourer '{unique_name}'")
    response = client.post(labourer_config.endpoint, json=payload)

    if response.status_code != 201:
        print(f"ERROR in created_labour fixture: {response.json()}")
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    labour = LabourerRead.model_validate(res.data)

    yield labour

    print(f"TEARDOWN: Deleting labourer {labour.id} ('{unique_name}')")
    client.delete(f'{labourer_config.endpoint}/{labour.id}')


@pytest.fixture
def created_sub_recipe(client: TestClient) -> RecipeRead:
    """Fixture to create a sub-recipe for prerequisite testing.  Same function as created_recipe, but with a different
    name to allow calling of both fixtures in the same test."""
    payload = recipe_config.create_payload.copy()
    unique_name = f"Test Sub-Recipe {fake.bs()} {datetime.now().isoformat()}"
    payload['recipe_name'] = unique_name

    print(f"SETUP: Creating sub-recipe '{unique_name}'")
    response = client.post(recipe_config.endpoint, json=payload)
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    recipe = RecipeRead.model_validate(res.data)

    yield recipe

    print(f"TEARDOWN: Deleting sub-recipe {recipe.recipe_id} ('{unique_name}')")
    client.delete(f'{recipe_config.endpoint}/{recipe.recipe_id}')

@pytest.fixture
def created_recipe_sub_recipe_link(
        client: TestClient,
        created_recipe: RecipeRead,
        created_sub_recipe: RecipeRead
) -> RecipeSubRecipeRead:
    """
    Fixture to create a complete recipe-sub-recipe link.
    It depends on two recipe fixtures and handles its own cleanup.
    """
    # SETUP: Create the link using fields from the RecipeSubRecipeCreate schema
    payload = {
        "parent_recipe_id": created_recipe.recipe_id,
        "sub_recipe_id": created_sub_recipe.recipe_id,
        "quantity": 1,
        "uom_id": 2,  # Assuming 2 is a valid UOM ID (e.g., 'each')
        "notes": "Initial test note for sub-recipe link.",
        "sort_order": 5
    }

    response = client.post(recipe_sub_recipe_config.endpoint, json=payload)
    assert response.status_code == 201
    res = ApiResponse.model_validate(response.json())
    link_object = RecipeSubRecipeRead.model_validate(res.data)

    yield link_object  # The test runs here

    # TEARDOWN: This guaranteed cleanup is key to robust tests
    print(f"TEARDOWN: Deleting recipe_sub_recipe link {link_object.id}")
    client.delete(f'{recipe_sub_recipe_config.endpoint}/{link_object.id}')


@pytest.fixture
def created_invoice(client: TestClient) -> InvoiceRead:
    """
    Fixture to create a new Invoice (empty)

    """
    print("SETUP: Creating a new invoice via GET /invoice/new")
    # This endpoint creates a new blank invoice; the pattern for the creation of an invoice is different to other
    # forms because the primary path for creating an invoice is via POSTing a PDF and having AI parse it.
    # To isoloate the test and avoid external calls an inconsistencies, the invoice is created via a GET request
    # manually.

    response = client.get("/invoice/new")

    if response.status_code != 200:
        print(f"ERROR in created_invoice fixture: {response.json()}")
    # The GET endpoint for creation likely returns 200 OK.
    assert response.status_code == 200

    res = ApiResponse.model_validate(response.json())
    invoice = InvoiceRead.model_validate(res.data)
    print(f"SETUP: Created invoice with ID {invoice.id}")

    yield invoice

    print(f"TEARDOWN: Deleting invoice {invoice.id}")
    delete_response = client.delete(f'/invoice/{invoice.id}')
    # According to the spec, the delete endpoint returns 202 Accepted.
    assert delete_response.status_code == 202


@pytest.fixture
def created_line_item(
        client: TestClient,
        created_invoice: InvoiceRead,
        created_buyable: BuyableRead
) -> LineItemRead:
    """
    Fixture to create a single LineItem for an existing invoice.
    Depends on the created_invoice fixture.
    Line items are created via the POST /invoice/lineitem endpoint and are linked directly to the invoice (no link table).
    """
    payload = {
        "invoice_id": created_invoice.id,
        "description": f"Test Line Item {fake.word()}",
        "cases": fake.random_int(min=1, max=5),
        "units": fake.random_int(min=1, max=10),
        "code": fake.ean(length=8),
        "value_ex_vat": float(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
        "vat_percentage": 20.0,
        "buyable_id": created_buyable.id,
        "unit_cost": float(fake.pydecimal(left_digits=2, right_digits=2, positive=True)),
        "buyable_quantity": 1
    }

    print(f"SETUP: Creating line item for invoice {created_invoice.id}")
    response = client.post('/invoice/lineitem', json=payload)

    if response.status_code != 201:
        print(f"ERROR in created_line_item fixture: {response.json()}")
    assert response.status_code == 201

    res = ApiResponse.model_validate(response.json())
    line_item = LineItemRead.model_validate(res.data)

    yield line_item

    print(f"TEARDOWN: Deleting line_item {line_item.id}")
    delete_response = client.delete(f'/invoice/lineitem/{line_item.id}')
    assert delete_response.status_code == 200


# Fixture provides the TestClient to all testa
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as tc:
        # intial_tidy_up()  // this shouldn't be necessary - the fixtures should take care of this during tear down
        yield tc