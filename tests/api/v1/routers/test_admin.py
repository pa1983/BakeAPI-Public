from app.models.uom import UnitOfMeasure
from app.models.title import Title
from app.models.currency import Currency
from app.models.supplier import Supplier # Assuming SupplierRead is aliased or available
from app.models.user import UserReadProfile # Using UserReadProfile for /user_info
from app.models.product_type import ProductTypeRead
from app.models.recipe_type import RecipeTypeRead
from app.models.recipe_status import RecipeStatusRead
from tests.fixtures import *
import json

class TestCommonEndpoints:
    """Tests for simple, read-only GET endpoints under the /common path."""

    def test_get_uom(self, client: TestClient):
        """Tests GET /common/uom - expects a raw list of UnitOfMeasure objects."""
        response = client.get("/common/uom")
        assert response.status_code == 200
        # Validate that the response is a list and each item conforms to the model
        data = [UnitOfMeasure.model_validate(item) for item in response.json()]
        assert isinstance(data, list)
        if data: # If the list is not empty, check the first item's type
            assert isinstance(data[0], UnitOfMeasure)

    def test_get_title(self, client: TestClient):
        """Tests GET /common/title - expects a raw list of Title objects."""
        response = client.get("/common/title")
        assert response.status_code == 200
        data = [Title.model_validate(item) for item in response.json()]
        assert isinstance(data, list)
        if data:
            assert isinstance(data[0], Title)

    def test_get_currency(self, client: TestClient):
        """Tests GET /common/currency - expects an ApiResponse containing a list."""
        response = client.get("/common/currency")
        assert response.status_code == 200
        # Currency endpoint was created and integrated with the front end early on, and was sent directly without
        # being wrapped in an ApiResponse.  Ideally it would be fixed, but as it's not critical, we'll just validate
        # the response here and consider refactoring in later versions

        # Validate that list items conform to the Currency model
        json_data = json.loads(response.text)['data']
        currencies = [Currency.model_validate(item) for item in json_data]
        assert isinstance(currencies, list)
        if currencies:
            assert isinstance(currencies[0], Currency)

    def test_get_supplier(self, client: TestClient):
        """Tests GET /common/supplier - expects a raw list of Supplier objects."""
        response = client.get("/common/supplier")
        assert response.status_code == 200
        # Note: Your swagger refers to Supplier, assuming a SupplierRead model is used
        data = [Supplier.model_validate(item) for item in response.json()]
        assert isinstance(data, list)
        if data:
            assert isinstance(data[0], Supplier)


    def test_get_product_type(self, client: TestClient):
        """Tests GET /common/product_type - expects an ApiResponse containing a list."""
        response = client.get("/common/product_type")
        assert response.status_code == 200
        api_response = ApiResponse.model_validate(response.json())
        assert isinstance(api_response.data, list)
        if api_response.data:
            [ProductTypeRead.model_validate(item) for item in api_response.data]

    def test_get_recipe_type(self, client: TestClient):
        """Tests GET /common/recipe_type - expects an ApiResponse containing a list."""
        response = client.get("/common/recipe_type")
        assert response.status_code == 200
        api_response = ApiResponse.model_validate(response.json())
        assert isinstance(api_response.data, list)
        if api_response.data:
            [RecipeTypeRead.model_validate(item) for item in api_response.data]

    def test_get_recipe_status(self, client: TestClient):
        """Tests GET /common/recipe_status - expects an ApiResponse containing a list."""
        response = client.get("/common/recipe_status")
        assert response.status_code == 200
        api_response = ApiResponse.model_validate(response.json())
        assert isinstance(api_response.data, list)
        if api_response.data:
            [RecipeStatusRead.model_validate(item) for item in api_response.data]