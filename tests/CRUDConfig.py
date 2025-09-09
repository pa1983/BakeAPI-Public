from dataclasses import dataclass
from typing import Dict, Any, Type
from sqlmodel import SQLModel

from app.models.user import UserReadProfile

# set up the dependancy override object - will be passed as the response to dependancy usage in place of normal function
# eliminating need for communications with the cognito auth server
mock_user_data = UserReadProfile(
    email_address="test@system.com",
    forename="System",
    surname="Test",
    short_title="Mr",
    phone="07841903012",
    role_id=7,
    organisation_id=3,
    cognito_sub_id="not-a-real-cognito-sub-id"
)

async def override_get_current_user() -> UserReadProfile:
    return mock_user_data


# class structure for items being passed to the generic crud test suite

@dataclass
class CRUDConfig:
    # URL for endpoint, e.g. "/recipe"
    endpoint: str
    # a valid JSON payload to be POSTed to create a new object
    create_payload: Dict[str, Any]
    # A valid JSON payload for a PATCH to update an existing endpoint
    update_payload: Dict[str, Any]
    # response field name to check
    check_field: str
    # the SQLModel type expected in response to a create request
    response_model: Type[SQLModel]
    # name of the pk id field
    pk_field: str = "id"
    check_unique: bool = True # defaults to try as this will almost always be required, just needs excluded in rare cases



