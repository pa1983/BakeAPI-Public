import math
from datetime import date, timedelta
from app.models.recipe_cost_analysis import RecipeCostAnalysis
from tests.generic_CRUD_test import assert_is_valid_api_response
from tests.fixtures import *

class TestRecipeCostAnalysis:
    """
    Test suite for validating the cost analysis functionality of the recipe endpoint
    """
    def test_get_cost_analysis(self,
                               client: TestClient,
                               created_line_item: LineItemRead,
                               created_buyable: BuyableRead,
                               created_ingredient: IngredientRead,
                               created_recipe: RecipeRead,
                               created_sub_recipe: RecipeRead
                               ):
        # build a recipe from scratch with known values for variables.  Use faker to produce random names to
        # avoid risk of conflicts if data has been left over from earlier tests

        ### LABOUR - as endpoints haven't yet been built to support the definition of labour rates or categories,
        ## test values have been manually inserted into the database.  This is not ideal, but it's the only way to
        ## get the tests working quickly.  A future version of the API will support labour rates and categories and these
        ## unit tests can be updated to reflect that.

        # these are the values used in the test data
        labour_rate_2025 = 16.5
        labour_rate_2024 = 15.5
        labour_rate_2023 = 14.5
        labourer_id = 86
        sub_recipe_quantity = 2.5

        # buyable's defaults, set in config:
        # "uom_id": 1,
        # "quantity": "100.0"

        ## 1 - create an invoice line item, which by default creates an invoice using the create_invoice fixture,
        # and a buyable using the created_buyable fixture.

        # 2 - now need to link the buyable to the ingredient to allow pricing data to flow through
        payload = {
            "ingredient_id": created_ingredient.ingredient_id,
            "buyable_id": created_buyable.id,
            "sort_order": 10,
            "notes": "Link ingredient to buyable."
        }
        response = client.post(ingredient_buyable_config.endpoint, json=payload)

        buyable_ingredient_data_object = assert_is_valid_api_response(response, 201, IngredientBuyableRead)
        assert buyable_ingredient_data_object.ingredient_id == created_ingredient.ingredient_id
        assert buyable_ingredient_data_object.buyable_id == created_buyable.id

        ## RECIPE LINKS - add the recipe ingredient, labour and sub-recipe links
        # 3 - link the ingredient to the recipe
        payload = {
            "recipe_id": created_recipe.recipe_id,
            "ingredient_id": created_ingredient.ingredient_id,
            "quantity": 500,
            "uom_id": 1,
            "notes": "Adding 500g of test ingredient to a test recipe."
        }
        response = client.post(recipe_ingredient_config.endpoint, json=payload)

        recipe_ingredient_data_object = assert_is_valid_api_response(response, 201, RecipeIngredientRead)
        assert recipe_ingredient_data_object.recipe_id == created_recipe.recipe_id
        assert recipe_ingredient_data_object.ingredient_id == created_ingredient.ingredient_id


        # 4 - link labour to the recipe

        payload = {
            "recipe_id": created_recipe.recipe_id,
            "labourer_id": labourer_id,
            "labour_minutes": 30,
            "labour_category_id": 1,
            "description": "Mixing and initial kneading."
        }
        response = client.post(recipe_labour_config.endpoint, json=payload)

        recipe_labour_data_object = assert_is_valid_api_response(response, 201, RecipeLabourRead)
        assert recipe_labour_data_object.recipe_id == created_recipe.recipe_id
        assert recipe_labour_data_object.labourer_id == labourer_id


        # 5 - create the sub recipe
        # SUB-RECIPE - need to build the sub recipe details that will be linked to the parent recipe.  Will use
        # exactly the same details as the parent recipe, but with no sub-recipe
        #- link the ingredient to the sub recipe
        payload = {
            "recipe_id": created_sub_recipe.recipe_id,
            "ingredient_id": created_ingredient.ingredient_id,
            "quantity": 500,
            "uom_id": 1,
            "notes": "Adding 500g of test ingredient to a test recipe."
        }
        response = client.post(recipe_ingredient_config.endpoint, json=payload)

        sub_recipe_ingredient_data_object = assert_is_valid_api_response(response, 201, RecipeIngredientRead)
        assert sub_recipe_ingredient_data_object.recipe_id == created_sub_recipe.recipe_id
        assert sub_recipe_ingredient_data_object.ingredient_id == created_ingredient.ingredient_id


        #  - link labour to the sub recipe

        payload = {
            "recipe_id": created_sub_recipe.recipe_id,
            "labourer_id": labourer_id,
            "labour_minutes": 30,
            "labour_category_id": 1,
            "description": "Mixing and initial kneading."
        }
        response = client.post(recipe_labour_config.endpoint, json=payload)

        sub_recipe_labour_data_object = assert_is_valid_api_response(response, 201, RecipeLabourRead)
        assert sub_recipe_labour_data_object.recipe_id == created_sub_recipe.recipe_id
        assert sub_recipe_labour_data_object.labourer_id == labourer_id

        # 5 - link the sub-recipe to the recipe. For testing purposes, will link to itself, but with a multiplier
        # for the quantity to check roll up logic.  This eliminates the need to create a separate recipe for the
        # sub-recipe - this is unnecessary since we have already tested the recipe logic

        payload = {
            "parent_recipe_id": created_recipe.recipe_id,
            "sub_recipe_id": created_sub_recipe.recipe_id,
            "quantity": sub_recipe_quantity,
            "uom_id": 9,  # same UOM as the parent recipe to avoid conflicts, 9 is pieces, i.e. batches of a full recipe
            "notes": "Adding 2.5 units of a sub-recipe.",
            "sort_order": 10
        }
        response = client.post(recipe_sub_recipe_config.endpoint, json=payload)

        recipe_sub_recipe_data_object = assert_is_valid_api_response(response, 201, RecipeSubRecipeRead)
        assert recipe_sub_recipe_data_object.parent_recipe_id == created_recipe.recipe_id
        assert recipe_sub_recipe_data_object.sub_recipe_id == created_sub_recipe.recipe_id

        # 6 - call the cost analysis endpoint
        print("Gathering test values...")
        # 7 - validate the response against manually calculated values

        ## INGREDIENTS
        # to calculate the ingredient cost, we need to get the linked buyable, then the line item cost from invoice
        # buyable - default for created buyable is 100 g

        # get the ingredient cost into base units
        ingredient_cost = float(created_line_item.unit_cost / created_buyable.quantity)
        recipe_ingredient_quantity = float(recipe_ingredient_data_object.quantity)
        recipe_ingredient_cost = float(recipe_ingredient_quantity * ingredient_cost)

        # ignoring UOM conversion at this point to simplify the test

        ## LABOUR
        ## get the recipe labour cost
        recipe_labour_cost = float(recipe_labour_data_object.labour_minutes) * (labour_rate_2025/60)

        # calculate the total cost of the recipe (a single batch)

        ## SUB-RECIPES
        # The sub recipe uses the same fixtures as recipe, so should be the same details as the recipe
        sub_recipe_quantity = recipe_sub_recipe_data_object.quantity  # the number of sub recipes consumed by the recipe
        # as we're using the same fixtures, the sub recipe quantity is the same as the recipe quantity, and thus the cost roll-up
        # above can be reused, we're just using the sub-recipe link up to calculate the number of sub-recipe batches
        # to roll up total costs.

        # Now have the total cost of one recipe (excluding sub-recipes):
        total_recipe_cost = recipe_ingredient_cost + recipe_labour_cost

        grand_total_cost = total_recipe_cost * (1 + (float(sub_recipe_quantity)/float(created_recipe.recipe_quantity) ))  # the initial recipe plus the number of sub-recipes

        # a recipe produces a nummber of units:
        quantity_produced = created_recipe.recipe_quantity  # the number of units produced by the recipe - required to calculate unit cost

        unit_cost = grand_total_cost / float(quantity_produced)

        # now compare this unit cost to the value returned from the endpoint

        # define a datepoint of TOMORROW so that the date of comparison is definitely AFTER the line item price point
        tomorrow = date.today() + timedelta(days=1)

        # Format the date object into an ISO standard string
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        cost_analysis_response = client.get(f'{recipe_config.endpoint}/{created_recipe.recipe_id}/cost-analysis?date_point={tomorrow_str}')
        assert cost_analysis_response.status_code == 200
        assert cost_analysis_response.text
        cost_analysis_response_json = cost_analysis_response.json()
        analysis_data_object = RecipeCostAnalysis.model_validate(cost_analysis_response_json['data'][0])
        assert type(analysis_data_object) == RecipeCostAnalysis
        # cost analysis response is a list of all components in the parent recipe, incluing sub-recipe components.  It
        # is formatted this way to allow front end charts to decide how they display data, and to what level of granularity
        # to test the result we need to aggregate the costs and compare to the calculated value.

        total_cost_from_api = sum(float(item['total_cost']) for item in cost_analysis_response_json['data'])
        response_unit_cost = total_cost_from_api/float(quantity_produced)
        # throughout the test, decimals have been converted to floats to avoid type conflicts between decimal and float.
        # This will lead to small but insignifical FP errors - allow for these in the comparison assertion.
        assert math.isclose(response_unit_cost, unit_cost, abs_tol=0.001)
        # all fixtures used in the whole function call chain are available, so no need to import individually

        # Clean up all items created in this test - they have to be cleared before the test completes in order
        # for the cleanup functions in the fixtures to be able to delete the linked items
        client.delete(f'{recipe_ingredient_config.endpoint}/{recipe_ingredient_data_object.recipe_id}')
        client.delete(f'{ingredient_buyable_config.endpoint}/{buyable_ingredient_data_object.id}')
        client.delete(f'{recipe_sub_recipe_config.endpoint}/{recipe_sub_recipe_data_object.id}')
        client.delete(f'{recipe_labour_config.endpoint}/{recipe_labour_data_object.id}')
        client.delete(f'{recipe_ingredient_config.endpoint}/{sub_recipe_ingredient_data_object.recipe_id}')
        client.delete(f'{recipe_labour_config.endpoint}/{sub_recipe_labour_data_object.id}')