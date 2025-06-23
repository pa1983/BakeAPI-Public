from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logging_config import logger

env_path = find_dotenv()
if not env_path:
    print("Warning - no env_path found ")
else:
    print(f'.env found at {env_path}')
    load_dotenv(env_path)

# env_file_location = r'..\..\.env'

class Settings(BaseSettings):
    # Project specific settings
    PROJECT_NAME: str   # todo - change this once agree on a project name with customer
    VERSION: str

    USER: str
    PASSWORD: str
    HOST: str
    PORT: str
    NAME: str

    # AWS S3 Settings  # todo - currently using wide open settings - once working, change to a bake-specific credential set
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET_NAME: str
    S3_BASE_URL: str

    # cognito user pool details
    AWS_COGNITO_USERPOOL_ID: str
    AWS_COGNITO_APP_CLIENT_ID: str
    AWS_COGNITO_TEST_USERNAME: str
    AWS_COGNITO_TEST_PASSWORD: str

    model_config = SettingsConfigDict(env_file=env_path, extra='ignore')

try:
    settings = Settings()
    logger.debug('Settings sucessfully loaded from .env')
except Exception as e:
    msg = f'Error loading settings from .env file - confirm .env file is present'
    logger.warning(msg)
    raise Exception(msg)

if __name__ == '__main__':
    for s in settings:
        print(s)