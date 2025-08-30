from fastapi.testclient import TestClient

from app.database.session import get_session

from app.dependencies.user_dependencies import get_current_user
from .CRUDConfig import override_get_current_user
from main import app


client = TestClient(app)


# override the get_current_user dependency, which passes back a validated user's details
app.dependency_overrides[get_current_user] = override_get_current_user

def test_read_get_invoices():
    response = client.get("/invoice/invoices")
    assert response.status_code == 200
    print(response.json())
    #TODO -  assert results match expected output type?  Assert all have the correct org id?  What else to test?