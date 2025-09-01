"""
Crud test suit for use in testing of join tables, e.g. recipe_ingredient - the test needs a recipe and ingredient
created in the DB before it can test the creation of the join
"""
from .generic_CRUD_test import assert_is_valid_api_response
from .test_configs import ingredient_buyable_config, ingredient_image_config, recipe_ingredient_config, \
    recipe_labour_config, recipe_sub_recipe_config, ingredient_config, buyable_config, recipe_config
from .fixtures import *


# todo - test image uploads - a little different to other tests so far as the image is sent to the ingredient endpoint, saved, then the link created without any need for awareness of the ID of the image DB entry
class TestIngredientBuyableJoin:
    """A specific and robust test suite for the Ingredient-Buyable relationship."""

    def test_create_link(self, client: TestClient, created_ingredient: IngredientRead, created_buyable: BuyableRead):
        """Test ONLY the creation of the link."""
        payload = {
            "ingredient_id": created_ingredient.ingredient_id,
            "buyable_id": created_buyable.id,
            "grams_per_unit": 100,  # from your config
            "supplier_id": 1  # from your config
        }
        response = client.post(ingredient_buyable_config.endpoint, json=payload)

        data_object = assert_is_valid_api_response(response, 201, IngredientBuyableRead)
        assert data_object.ingredient_id == created_ingredient.ingredient_id
        assert data_object.buyable_id == created_buyable.id

        # clean up the item created IN THIS test to keep it atomic.
        client.delete(f'{ingredient_buyable_config.endpoint}/{data_object.id}')

    def test_create_link_conflict(self, client: TestClient, created_ingredient_buyable_link: IngredientBuyableRead):
        """Test that creating a duplicate link results in a conflict error."""
        # The created_ingredient_buyable_link fixture has already created one link.
        # Now, try to create the exact same one again.
        payload = {
            "ingredient_id": created_ingredient_buyable_link.ingredient_id,
            "buyable_id": created_ingredient_buyable_link.buyable_id,
            "sort_order": 100,
            "note": "I'm a note"
        }
        response = client.post(ingredient_buyable_config.endpoint, json=payload)
        assert_is_valid_api_response(response, 409)  # 409 Conflict

    def test_get_one_link(self, client: TestClient, created_ingredient_buyable_link: IngredientBuyableRead):
        """Test retrieving a single link by its ID."""
        # The fixture provides the link, we just need to test the GET.
        link_id = created_ingredient_buyable_link.id
        response = client.get(f'{ingredient_buyable_config.endpoint}/{link_id}')

        data_object = assert_is_valid_api_response(response, 200, IngredientBuyableRead)
        assert data_object.id == link_id
        assert data_object.ingredient_id == created_ingredient_buyable_link.ingredient_id

    def test_update_link(self, client: TestClient, created_ingredient_buyable_link: IngredientBuyableRead):
        """Test updating an existing link."""
        # The fixture provides the link to be updated.
        link_id = created_ingredient_buyable_link.id
        PATCHED_NOTE = "I've been patched"
        update_payload = {"notes": PATCHED_NOTE}  # Example update

        response = client.patch(f'{ingredient_buyable_config.endpoint}/{link_id}', json=update_payload)

        data_object = assert_is_valid_api_response(response, 200, IngredientBuyableRead)
        assert data_object.id == link_id
        assert data_object.notes == PATCHED_NOTE  # Verify the change was applied

    def test_delete_link(self, client: TestClient, created_ingredient: IngredientRead, created_buyable: BuyableRead):
        """Test the deletion of a link and its idempotency."""
        # This test needs to control its own creation/deletion to verify the outcome.
        # So we don't use the 'created_ingredient_buyable_link' fixture here.
        payload = {
            "ingredient_id": created_ingredient.ingredient_id,
            "buyable_id": created_buyable.id,
            "sort_order": 10,
            "notes": "I'm a note"
        }
        create_response = client.post(ingredient_buyable_config.endpoint, json=payload)
        link_object = IngredientBuyableRead.model_validate(ApiResponse.model_validate(create_response.json()).data)
        link_id = link_object.id

        # HAPPY PATH - Delete the link
        delete_response = client.delete(f'{ingredient_buyable_config.endpoint}/{link_id}')
        assert_is_valid_api_response(delete_response, 200)

        # UNHAPPY PATH - Verify it's gone by trying to delete again
        second_delete_response = client.delete(f'{ingredient_buyable_config.endpoint}/{link_id}')
        assert_is_valid_api_response(second_delete_response, 404)
