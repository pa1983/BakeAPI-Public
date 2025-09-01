import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, text
from app.database.session import engine

from app.models.common import ApiResponse

from .CRUDConfig import CRUDConfig
from .test_configs import generic_crud_configs
from .fixtures import client
# set the dependency override to provide authentication and a sample user (the TEST user) to all tests


#
# def intial_tidy_up():
#     """Tidy up after tests are run to ensure there are no residual entries left behind from an earlier test suite that failed
#     as these could cause unexpected behaviour in subsequent tests."""
#     print("running tidy up")
#     # todo - do i want this here?  will it throw off any fixtures?  shouldn't really be necessary if fixtures have worked?  but they could fail or stop early...
#     with Session(engine) as session:
#         session.exec(text("DELETE i.* FROM ingredient i where organisation_id = 3;"))
#         session.commit()

# Helper function to reduce repetition - checking ApiResponse object is repeated in all tests
def assert_is_valid_api_response(response, expected_status: int, expected_data_model = None):
    """Asserts that the response is a valid ApiResponse and checks its contents."""
    assert response.status_code == expected_status
    assert response.text
    # the data response SHOULD ALWAYS be an ApiResponse object - if not the test should fail
    res = ApiResponse.model_validate(response.json())
    assert isinstance(res, ApiResponse)
    # check that there's a message of between 1 and 200 chars - all messages should have a length >  0 to be meanuingful
    # messages that are very long are likely to be an unintentional leak of data that might pose a security risk, e.g.
    # an error message that contains a full error traceback instead of a sanitised user-friendly response
    assert 250 > len(res.message) > 0
    if expected_data_model:
        # check that the data object in the API Response fits the expected data model by running model_validate against the data
        data_object = expected_data_model.model_validate(res.data)
        assert isinstance(data_object, expected_data_model)
        return data_object
    else:
        assert res.data is None
        return None




@pytest.fixture
def created_item(client: TestClient, config: CRUDConfig):
    """Fixture to create an item for use in tests. Creating an item for each test, rather than using an item
    made in the 'create' part of the test suite, ensures that all tests are independent of each other."""
    # SETUP - Create the item
    response = client.post(config.endpoint, json=config.create_payload)
    assert response.status_code == 201
    res = ApiResponse.model_validate(response.json())
    created_obj = config.response_model.model_validate(res.data)
    item_id = getattr(created_obj, config.pk_field)

    yield created_obj # The test runs at this point

    # TEARDOWN: Delete the item to ensure cleanup and full atomicity of each test element
    client.delete(f'{config.endpoint}/{item_id}')

# The parametrize decorator iterates through the configs passed from all_crud_configs and makes each element
# available as 'config' to all functions in the class
@pytest.mark.parametrize("config", generic_crud_configs)
class TestGenericCRUD:
    """A Generic Test Suite for CRUD Endpoints"""

    def test_create_and_conflict(self, client: TestClient, config: CRUDConfig):
        """Test create endpoint and unique constraints"""
        ## HAPPY PATH ##
        response = client.post(config.endpoint, json=config.create_payload)
        data_object = assert_is_valid_api_response(response, 201, config.response_model)
        assert getattr(data_object, config.check_field) == config.create_payload[config.check_field]
        item_id = getattr(data_object, config.pk_field)
        ## UNHAPPY PATH - CONFLICT ##
        if config.check_unique:
            # in some instances, don't want to check for uniqueness, e.g. in invoice line items it's conceivable that
            # the same item is legitimately repeated in the same invoice - so we skip this check in that case
            conflict_response = client.post(config.endpoint, json=config.create_payload)
            assert_is_valid_api_response(conflict_response, 409)

        # Cleanup the item created in this test
        client.delete(f'{config.endpoint}/{item_id}')

    def test_get_all(self, client: TestClient, config: CRUDConfig, created_item):
        """Test get all endpoint."""
        created_item_id = getattr(created_item, config.pk_field)
        response = client.get(f'{config.endpoint}/all')
        assert response.status_code == 200
        res = ApiResponse.model_validate(response.json())
        all_elements = [config.response_model.model_validate(el) for el in res.data]

        # Find our created item in the list
        found_item = next((item for item in all_elements if getattr(item, config.pk_field) == created_item_id), None)
        assert found_item is not None
        assert isinstance(found_item, config.response_model)


    def test_get_one(self, client: TestClient, config: CRUDConfig, created_item):
        """Test get one by id endpoint."""
        item_id = getattr(created_item, config.pk_field)
        response = client.get(f'{config.endpoint}/{item_id}')
        data_object = assert_is_valid_api_response(response, 200, config.response_model)
        assert getattr(data_object, config.pk_field) == item_id

    def test_update(self, client: TestClient, config: CRUDConfig, created_item):
        """Test the update endpoint."""
        item_id = getattr(created_item, config.pk_field)
        response = client.patch(f'{config.endpoint}/{item_id}', json=config.update_payload)
        data_object = assert_is_valid_api_response(response, 200, config.response_model)
        assert getattr(data_object, config.pk_field) == item_id
        # Also assert that the change was actually applied
        assert getattr(data_object, config.check_field) == config.update_payload[config.check_field]

    def test_delete (self, client: TestClient, config: CRUDConfig, created_item):
        """Test the delete endpoint and its idempotency."""
        item_id = getattr(created_item, config.pk_field)
        ## HAPPY PATH ##
        response = client.delete(f'{config.endpoint}/{item_id}')
        # in hindsight this should be status 204, but would break usages in front end that expect an ApiResponse with a message to flash
        assert_is_valid_api_response(response, 200)

        ## UNHAPPY PATH - DELETE SAME ID AGAIN ##
        second_response = client.delete(f'{config.endpoint}/{item_id}')
        assert_is_valid_api_response(second_response, 404)



