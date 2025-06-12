from typing import Generator

from sqlmodel import create_engine, Session
from pydantic_settings import BaseSettings
from app.core.config import settings


DATABASE_URL = f"mysql+pymysql://{settings.USER}:{settings.PASSWORD}@{settings.HOST}:{settings.PORT}/{settings.NAME}"

# the first time create_engine is called, a connection will be created.  Subsequent calls will use the existing engine if available
# the underlying SQLAlchemy functionality takes care of connection pooling automatically
engine = create_engine(DATABASE_URL)


# session helper function - keeps session code as concise as possible in all DB calls
def get_session() -> Generator[Session, None, None]:
    """
    Yields a database session from the engine's connection pool.
    Ensures the session is closed after use.
    """
    with Session(engine) as session:
        yield session

# usage pattern - import this package:
# from database.session import get_session
# with get_session() as session:
#     session.add(xxx)
#     session.commit()
#     session.refresh(xxx)
#

if __name__ == "__main__":
    print(engine)

