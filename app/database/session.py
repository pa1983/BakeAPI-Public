from contextlib import contextmanager
from typing import Generator

from sqlmodel import create_engine, Session
from pydantic_settings import BaseSettings
from app.core.config import settings


DATABASE_URL = f"mysql+pymysql://{settings.USER}:{settings.PASSWORD}@{settings.HOST}:{settings.PORT}/{settings.NAME}"

# the first time create_engine is called, a connection will be created.  Subsequent calls will use the existing engine if available
# the underlying SQLAlchemy functionality takes care of connection pooling automatically
engine = create_engine(DATABASE_URL)



def get_session() -> Generator[Session, None, None]:
    """
    Session helper function for use within FastAPI DB calls via dependancies- keeps session code as concise as possible in all DB calls
    Yields a database session from the engine's connection pool.
    Ensures the session is closed after use.

    usage pattern - import this package:

    from database.session import get_session

    session: Session = Depends(get_session)
    session.exec(statement)
    session.commit()

    """
    with Session(engine) as session:
        yield session

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    A context manager for providing a database session for non-FastAPI use.
    """
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    print(engine)

