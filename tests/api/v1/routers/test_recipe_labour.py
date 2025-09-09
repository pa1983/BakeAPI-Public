from decimal import Decimal

from tests.generic_CRUD_test import assert_is_valid_api_response
from tests.test_configs import recipe_labour_config
from tests.fixtures import * # Imports all your fixtures

# Import the specific response model needed for validation
from app.models.recipe_labour import RecipeLabourRead


class TestRecipeLabourJoin:
    """A specific and robust test suite for the Recipe-Labour relationship."""

    def test_create_link(self, client: TestClient, created_recipe: RecipeRead, created_labour: LabourerRead):
        """Test ONLY the creation of the link."""
        payload = {
            "recipe_id": created_recipe.recipe_id,
            "labourer_id": created_labour.id,
            "labour_minutes": 30,
            "labour_category_id": 1,
            "description": "Mixing and initial kneading."
        }
        response = client.post(recipe_labour_config.endpoint, json=payload)

        data_object = assert_is_valid_api_response(response, 201, RecipeLabourRead)
        assert data_object.recipe_id == created_recipe.recipe_id
        assert data_object.labourer_id == created_labour.id

        # We must clean up the item created IN THIS test to keep it atomic.
        client.delete(f'{recipe_labour_config.endpoint}/{data_object.id}')

    # No conflict test is needed as a labour type can be added multiple times to the same recipe

    def test_get_one_link(self, client: TestClient, created_recipe_labour_link: RecipeLabourRead):
        """Test retrieving a single link by its ID."""
        # The fixture provides the link, we just need to test the GET.
        link_id = created_recipe_labour_link.id
        response = client.get(f'{recipe_labour_config.endpoint}/{link_id}')

        data_object = assert_is_valid_api_response(response, 200, RecipeLabourRead)
        assert data_object.id == link_id
        assert data_object.recipe_id == created_recipe_labour_link.recipe_id

    def test_update_link(self, client: TestClient, created_recipe_labour_link: RecipeLabourRead):
        """Test updating an existing link."""
        # The fixture provides the link to be updated.
        link_id = created_recipe_labour_link.id
        # Based on Swagger, 'labour_minutes' is an updatable field.
        UPDATED_MINUTES = "99.0"  # DB returns the time in decimal, so must do update and comparison in decimal for accurate comparison
        update_payload = {"labour_minutes": UPDATED_MINUTES}

        response = client.patch(f'{recipe_labour_config.endpoint}/{link_id}', json=update_payload)

        data_object = assert_is_valid_api_response(response, 200, RecipeLabourRead)
        assert data_object.id == link_id
        assert data_object.labour_minutes == Decimal(UPDATED_MINUTES)  # Verify the change was applied. # DB returns the time in decimal, so must do update and comparison in decimal for accurate comparison

    def test_delete_link(self, client: TestClient, created_recipe: RecipeRead, created_labour: LabourerRead):
        """Test the deletion of a link and its idempotency."""
        # This test needs to control its own creation/deletion to verify the outcome.
        payload = {
            "recipe_id": created_recipe.recipe_id,
            "labourer_id": created_labour.id,
            "labour_minutes": 5,
            "labour_category_id": 2,
            "description": "This link will be deleted."
        }
        create_response = client.post(recipe_labour_config.endpoint, json=payload)
        link_object = RecipeLabourRead.model_validate(ApiResponse.model_validate(create_response.json()).data)
        link_id = link_object.id

        # HAPPY PATH - Delete the link
        delete_response = client.delete(f'{recipe_labour_config.endpoint}/{link_id}')
        assert_is_valid_api_response(delete_response, 200)

        # UNHAPPY PATH - Verify it's gone by trying to delete again
        second_delete_response = client.delete(f'{recipe_labour_config.endpoint}/{link_id}')
        assert_is_valid_api_response(second_delete_response, 404)