
from typing import Dict, Any
import boto3
from fastapi_cognito import CognitoAuth, CognitoSettings
from app.core.config import settings


class MyCognitoSettings(CognitoSettings):
    userpools: Dict[str, Any] = {
        "bakeonomics_userpool": {
            "region": settings.AWS_REGION,
            "userpool_id": settings.AWS_COGNITO_USERPOOL_ID,
            "app_client_id": settings.AWS_COGNITO_APP_CLIENT_ID
        }
    }
    check_expiration: bool = True
    jwt_header_name: str = "Authorization"
    jwt_header_prefix: str = "Bearer"


cogito_settings = MyCognitoSettings()

cognito_auth = CognitoAuth(
    settings=cogito_settings
)

def get_cognito_tokens(client_id, username, password):
    client = boto3.client('cognito-idp')
    try:
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
            },
            ClientId=client_id
        )
        return response['AuthenticationResult']
    except client.exceptions.NotAuthorizedException:
        print("Incorrect username or password.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_auth_token():
    tokens = get_cognito_tokens(settings.AWS_COGNITO_APP_CLIENT_ID,
                                settings.AWS_COGNITO_TEST_USERNAME,
                                settings.AWS_COGNITO_TEST_PASSWORD)

    if tokens:

        access_token = tokens.get('AccessToken')
        print(tokens.get('AccessToken'))
        return access_token

    else:
        print("Failed to get tokens.")
        return None



if __name__ == '__main__':
    get_auth_token()
    # todo - figure out how to authorise in postman to avoid manually grabbing token
# todo - write tests to ensure that the test username creates valid token.  Pass in invalid user and password to confirm auth rejects correctly also.