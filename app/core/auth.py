#core/auth.py
# testing cognito - get access token without using front end login for testing API endpoints
from typing import Dict, Any

import boto3
from fastapi import Depends, status
from sqlalchemy.orm import selectinload

from app.models.user import User, Organisation
from app.models.role import Role, RolePermissionLink
from sqlmodel import Session, select
from fastapi_cognito import CognitoAuth, CognitoSettings

from app.core.config import settings
from app.database.session import engine, get_session


# Note the unused imports are required below to ensure that model classes are available for use by type checking when
# classes are specified as string literals to avoid circular dependencies

from app.models.ingredient import Ingredient, Ingredient_Image, IngredientRead
from app.models.ingredient_image import *
from app.models.uom import *
from app.models.image import *
from app.models.user import *
from app.models.organisation import *
from app.models.permission import Permission


class MyCognitoSettings(CognitoSettings):
    userpools: Dict[str, Any] = {
        "bokeonomics_userpool": {
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

# CognitoToken(origin_jti='9eee907d-660a-4e08-aa0c-4f722cf07ae0', cognito_id='d2e5a494-2061-7025-bc08-2c55e8066af6', event_id='cc506764-57de-4464-b148-623b957f98d6', token_use='access', scope='aws.cognito.signin.user.admin', auth_time=1750164289, iss=HttpUrl('https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_l4pSAAZYP'), exp=1750167889, iat=1750164289, jti='c7e2d217-b1a2-42e1-ac47-4cbd1d5cc39a', client_id='4ph7lbuua09u9qstvlc6mf2i4', username='d2e5a494-2061-7025-bc08-2c55e8066af6')

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


def get_tokens_for_testing():
    tokens = get_cognito_tokens(settings.AWS_COGNITO_APP_CLIENT_ID,
                                settings.AWS_COGNITO_TEST_USERNAME,
                                settings.AWS_COGNITO_TEST_PASSWORD)

    if tokens:

        print("ID Token:", tokens.get('IdToken'))
        print("Access Token:", tokens.get('AccessToken'))
        print("Refresh Token:", tokens.get('RefreshToken'))
    else:
        print("Failed to get tokens.")


if __name__ == '__main__':
    get_tokens_for_testing()
# todo - write tests to ensure that the test username creates valid token.  Pass in invalid user and password to confirm auth rejects correctly also.

# ID Token: eyJraWQiOiJMaURmdVdmWHh2RlRUMXAxZlJyYTRiNkw0SkwzdHdwU2tWbTYyT1wvczVmRT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkMmU1YTQ5NC0yMDYxLTcwMjUtYmMwOC0yYzU1ZTgwNjZhZjYiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfbDRwU0FBWllQIiwiY29nbml0bzp1c2VybmFtZSI6ImQyZTVhNDk0LTIwNjEtNzAyNS1iYzA4LTJjNTVlODA2NmFmNiIsIm9yaWdpbl9qdGkiOiI5YWQwNzJkOS1hZjg3LTQ1NWQtYjdjOS0xZGFjMGEwNWIwOTEiLCJhdWQiOiI0cGg3bGJ1dWEwOXU5cXN0dmxjNm1mMmk0IiwiZXZlbnRfaWQiOiJhZWM0N2M4MC04MTZmLTRhMDEtOGYwNi0zMGExNDcwNzE5MWYiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc0OTIyMTU4MiwiZXhwIjoxNzQ5MjI1MTgyLCJpYXQiOjE3NDkyMjE1ODIsImp0aSI6ImI3Mzg1ZjRmLTljYjQtNGU4Yi04OTM4LTZlZDg4YWNhMjAzMSIsImVtYWlsIjoicGExOTgzQGdtYWlsLmNvbSJ9.bIdE0frO3bMGYjELQLs6A_LYS9BayfsK3qsjzJGjMKY-T6884z90Kgq35G4OL0K3AJPtw7GB25wMuE03b0EHcv0y3tM5w8r_V0-F2G35YZcyGq9AOmGJbU9kazre7Hx96OsT14MGbzXvZJNqupMpRo9bffHPNk_Qp5yAKBzWtVWgAvSi9-1E8a_FhX_VaE6KFwYpRg1PP0K-y6qEHyy-WZm1XCB62lfnpdz3n_KZF9eXzNx1n4bvJaneLRbvDOYadAzBTzpQmaiMK2bFn_i-BUQK9qTmSUS79AMslT-3HRKFDSIlBDa3HIsGSMRol4vV5gQCpyEoJq7XF5blj_mOZA
# Access Token: eyJraWQiOiJnU2dFNTdONEpFOUNLeTFoREdqcWlNUUU5c2JWcHRMd0s5VkZ3Y1BoT1RFPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMmU1YTQ5NC0yMDYxLTcwMjUtYmMwOC0yYzU1ZTgwNjZhZjYiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9sNHBTQUFaWVAiLCJjbGllbnRfaWQiOiI0cGg3bGJ1dWEwOXU5cXN0dmxjNm1mMmk0Iiwib3JpZ2luX2p0aSI6IjlhZDA3MmQ5LWFmODctNDU1ZC1iN2M5LTFkYWMwYTA1YjA5MSIsImV2ZW50X2lkIjoiYWVjNDdjODAtODE2Zi00YTAxLThmMDYtMzBhMTQ3MDcxOTFmIiwidG9rZW5fdXNlIjoiYWNjZXNzIiwic2NvcGUiOiJhd3MuY29nbml0by5zaWduaW4udXNlci5hZG1pbiIsImF1dGhfdGltZSI6MTc0OTIyMTU4MiwiZXhwIjoxNzQ5MjI1MTgyLCJpYXQiOjE3NDkyMjE1ODIsImp0aSI6IjA5MjFlOTNjLTY1ZmItNDMwNi1hNGQ2LWM2ZDE2NThjZDdlNCIsInVzZXJuYW1lIjoiZDJlNWE0OTQtMjA2MS03MDI1LWJjMDgtMmM1NWU4MDY2YWY2In0.Y60q9CiY4-4__2R9jW197O0q4X-Qc6YzNHPRkkzMtV95nGf2AZuZvZ7mQM8fH4S8-Y0Or53dVqgLLhoYwMk0URKPOtzenRY9Ug2Ui7VxsdBcD8r93rFh3bKtPPzqf9yqHSGsQqNu2xJK_K1IxAU09t7YO9JzxthdyS8Ja4xIjeOhO66U6VW-h9E3S-aTyEt5Au2PZwhl5bVty11eiQzWmlt6U28I2tSEWXUTflSsQjcavo7tk7q4PoGogkHfX8s52GbaZ7eN6gF_BReNKUhq6TTtzUh7m4IZBS873IAx-Nr3iFuomeU6Lk4ZTPuNXuh6c3dHWsCD-yQ-WgmYDqT_TQ
# Refresh Token: eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.YLQUwMkW0WYog6puU3Hsferbk1wTqjrQ6sN2gTnW1L-IrIdlfmWWebQSyxe4WR4sgwogTOs8OqbetTil8fUjyxIJenXoeHsjahtXateuJaI4pEqWbGpl2MUc7orbPqofcjmKADJFgSLgK4y9nCCTDyFAEHiASaQ44wBrvEyh_1iRoqkndGsi2VocM-YMq-8l359xdrEFcVzPzDuxZ1eVq6lWkVgoNu56tpVIq8AOYwEvZPW5btGT8pbMdmb7u3IBQE_QFZgqTsuTxWR4g8jtYUXsAvOQ7hF7zRTtIcsw5N6SIALamhffpdgTspdcujYFTjCiRg446AxG7s2u0DX3MQ.rjYfJqkBQN4zliwq.4AuaQum7KVzuJ5ssBk2nIO9D_fVMiiDcyXLcdwfwPpFKZxElzg8xZcBL7jf5PxWrU17gpPONNuf1PyJFsllC-lfSMjV5aRXU2E5EnG3Z2rjXiPzh_x2epxjL-wSWcP5qo_-9Kh7cJWiAcVeBmaT-7pe8vSGcThpsEkiGnZIg4tujVI87AhByCT941Wb4XRvL7IpzYKzciTql1lFwIrTzxIxMlNht7kAhRHifjO2wM97PcTZW1TVGfPOV8uKLUC9V2pgHSPeFR-j519bUr5z5Y9JZ4zEymyIYt6K7ZyU832FQlRfleN52klT5UbZOcF0UA7GBcA7t3x6ShmM5XQ0tdRVUqhJjw4MpCba8xoLoo72KnO48zpZmNspQS9RV922QEcc5c3S4QSvpoE6LxbgzbI5re1lGjm-gg9QpNxJIyASCVrHVlo69PPsFQI-f5oc5XitxzXowxJ8BObnwH6MuJLHtp5FcS4H2XVSzGp7T2DQxAXUpKLNK_P9ivJGUmlJIRpuDNbLbAy_SPYnEmgTErE3wIYw7tJ4HyhE2vB_NazgCE7NhWso1l-D0BlwffFcO-l7inSQlf_H1YnQJcai1if9qgf0pGP1I0WmZU3nw58ooRFxZ_JJGUZQO-995X6zsRnA0SSQHfEt8UDN1cplF8E99NUJ5VMKt4NVSpSUYRflYYiiK6vm9GG8ztdKeo-aeYgoM9ATMuHRvivijZj49odCIuhfHHnldoJvkBaGBG7rYcM0Ed-_lFBP1gL7VHPrOruyfnQoPBuvfO-2jQ2XWPuYsw8GyD9OIc-A-6KOmDOVbtehvZvoF0-Q5_q_I-ULpXF4xFwb7DyBLI0zOZbd5P1U5C-woHNByEnoFPqLmJKS0oLn40IQxIIs-c52KTji-tH_IG1Yo7q6fvO0D-2TyS9tpv6T6X99fMHiCbmRejE6iTxsN4T3zybWWOrcPc90NFcowiuX7tobEIELDYrtsXsXj5xqHa3aAdV6Hiu21ODDnfDOO2mXJYom4xow0IvSSvVNHhrlMUkUgJIza5sp9llHBdMwGVoz__Imq2vZsLB3ZUI_bvEswSvohd6uBAfbLCez7_R2iAMrNkMdZHkQqqChwRxgsjv3fRkb3owtdhQV2HcD1dq9twd520snMriYwgtse825Tm8UBomN73Gwt4t_sV8g2fQPDFLEzhsX-L5PGKNAJHoSp4dDPP0BOntj-mPxcejaDNneta2rWmiJnf4XZO7yh-li1m7m4qKkVl8Cv7Apx1lfl-P0p2wDSQY6XNFiZ4DUfD9z61ZOD7nWbPR6HfA2C2i_APJFHBozJw_vai-9Yle216zGgbSXzoA.AaC_MNPvZIGXt8zRvRExpQ
