from tests.generic_CRUD_test import assert_is_valid_api_response
from tests.test_configs import recipe_ingredient_config
from tests.fixtures import * # Imports all your fixtures

# Import the specific response model needed for validation
from app.models.recipe_ingredient import RecipeIngredientRead

class TestRecipeIngredientJoin:
    """A specific and robust test suite for the Recipe-Ingredient relationship."""

    def test_create_link(self, client: TestClient, created_recipe: RecipeRead, created_ingredient: IngredientRead):
        """Test ONLY the creation of the link."""
        payload = {
            "recipe_id": created_recipe.recipe_id,
            "ingredient_id": created_ingredient.ingredient_id,
            "quantity": 500,
            "uom_id": 1,
            "notes": "Adding 500g of test ingredient to a test recipe."
        }
        response = client.post(recipe_ingredient_config.endpoint, json=payload)

        data_object = assert_is_valid_api_response(response, 201, RecipeIngredientRead)
        assert data_object.recipe_id == created_recipe.recipe_id
        assert data_object.ingredient_id == created_ingredient.ingredient_id

        # We must clean up the item created IN THIS test to keep it atomic.
        client.delete(f'{recipe_ingredient_config.endpoint}/{data_object.recipe_id}')

        # No conflict test is needed as an ingredient can be added multiple times to the same recipe

    def test_get_one_link(self, client: TestClient, created_recipe_ingredient_link: RecipeIngredientRead):
        """Test retrieving a single link by its ID."""
        # The fixture provides the link, we just need to test the GET.
        link_id = created_recipe_ingredient_link.id
        response = client.get(f'{recipe_ingredient_config.endpoint}/{link_id}')

        data_object = assert_is_valid_api_response(response, 200, RecipeIngredientRead)
        assert data_object.id == link_id
        assert data_object.recipe_id == created_recipe_ingredient_link.recipe_id

    def test_update_link(self, client: TestClient, created_recipe_ingredient_link: RecipeIngredientRead):
        """Test updating an existing link."""
        # The fixture provides the link to be updated.
        link_id = created_recipe_ingredient_link.id
        PATCHED_NOTE = "This note has been updated by a test."
        update_payload = {"notes": PATCHED_NOTE}

        response = client.patch(f'{recipe_ingredient_config.endpoint}/{link_id}', json=update_payload)

        data_object = assert_is_valid_api_response(response, 200, RecipeIngredientRead)
        assert data_object.id == link_id
        assert data_object.notes == PATCHED_NOTE  # Verify the change was applied

    def test_delete_link(self, client: TestClient, created_recipe: RecipeRead, created_ingredient: IngredientRead):
        """Test the deletion of a link and its idempotency."""
        # This test needs to control its own creation/deletion to verify the outcome.
        payload = {
            "recipe_id": created_recipe.recipe_id,
            "ingredient_id": created_ingredient.ingredient_id,
            "quantity": 10,
            "uom_id": 2,
            "notes": "This link will be deleted."
        }
        create_response = client.post(recipe_ingredient_config.endpoint, json=payload)
        link_object = RecipeIngredientRead.model_validate(ApiResponse.model_validate(create_response.json()).data)
        link_id = link_object.id

        # HAPPY PATH - Delete the link
        delete_response = client.delete(f'{recipe_ingredient_config.endpoint}/{link_id}')
        assert_is_valid_api_response(delete_response, 200)

        # UNHAPPY PATH - Verify it's gone by trying to delete again
        second_delete_response = client.delete(f'{recipe_ingredient_config.endpoint}/{link_id}')
        assert_is_valid_api_response(second_delete_response, 404)