from tests.generic_CRUD_test import assert_is_valid_api_response
from tests.test_configs import recipe_sub_recipe_config
from tests.fixtures import *

from app.models.recipe_sub_recipe import RecipeSubRecipeRead


class TestRecipeSubRecipeJoin:
    """A specific and robust test suite for the Recipe-Sub-Recipe relationship."""

    def test_create_link(self, client: TestClient, created_recipe: RecipeRead, created_sub_recipe: RecipeRead):
        """Test ONLY the creation of the link."""
        payload = {
            "parent_recipe_id": created_recipe.recipe_id,
            "sub_recipe_id": created_sub_recipe.recipe_id,
            "quantity": 2.5,
            "uom_id": 1,
            "notes": "Adding 2.5 units of a sub-recipe.",
            "sort_order": 10
        }
        response = client.post(recipe_sub_recipe_config.endpoint, json=payload)

        data_object = assert_is_valid_api_response(response, 201, RecipeSubRecipeRead)
        assert data_object.parent_recipe_id == created_recipe.recipe_id
        assert data_object.sub_recipe_id == created_sub_recipe.recipe_id

        # We must clean up the item created IN THIS test to keep it atomic.
        client.delete(f'{recipe_sub_recipe_config.endpoint}/{data_object.id}')

    # No conflict test is needed as a sub-recipe could potentially be added multiple times.

    def test_get_one_link(self, client: TestClient, created_recipe_sub_recipe_link: RecipeSubRecipeRead):
        """Test retrieving a single link by its ID."""
        # The fixture provides the link, we just need to test the GET.
        link_id = created_recipe_sub_recipe_link.id
        response = client.get(f'{recipe_sub_recipe_config.endpoint}/{link_id}')

        data_object = assert_is_valid_api_response(response, 200, RecipeSubRecipeRead)
        assert data_object.id == link_id
        assert data_object.parent_recipe_id == created_recipe_sub_recipe_link.parent_recipe_id

    def test_update_link(self, client: TestClient, created_recipe_sub_recipe_link: RecipeSubRecipeRead):
        """Test updating an existing link."""
        # The fixture provides the link to be updated.
        link_id = created_recipe_sub_recipe_link.id
        # Based on Swagger, 'notes' is an updatable field.
        PATCHED_NOTE = "This sub-recipe note has been updated by a test."
        update_payload = {"notes": PATCHED_NOTE}

        response = client.patch(f'{recipe_sub_recipe_config.endpoint}/{link_id}', json=update_payload)

        data_object = assert_is_valid_api_response(response, 200, RecipeSubRecipeRead)
        assert data_object.id == link_id
        assert data_object.notes == PATCHED_NOTE  # Verify the change was applied

    def test_delete_link(self, client: TestClient, created_recipe: RecipeRead, created_sub_recipe: RecipeRead):
        """Test the deletion of a link and its idempotency."""
        # This test needs to control its own creation/deletion to verify the outcome.
        payload = {
            "parent_recipe_id": created_recipe.recipe_id,
            "sub_recipe_id": created_sub_recipe.recipe_id,
            "quantity": 1,
            "uom_id": 2,
            "notes": "This link will be deleted.",
            "sort_order": 20
        }
        create_response = client.post(recipe_sub_recipe_config.endpoint, json=payload)
        link_object = RecipeSubRecipeRead.model_validate(ApiResponse.model_validate(create_response.json()).data)
        link_id = link_object.id

        # HAPPY PATH - Delete the link
        delete_response = client.delete(f'{recipe_sub_recipe_config.endpoint}/{link_id}')
        assert_is_valid_api_response(delete_response, 200)

        # UNHAPPY PATH - Verify it's gone by trying to delete again
        second_delete_response = client.delete(f'{recipe_sub_recipe_config.endpoint}/{link_id}')
        assert_is_valid_api_response(second_delete_response, 404)