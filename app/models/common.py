from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    Standard response type to be used by most API response.
    Message should be overridden, as required, to show a meaningful, user-friendly message that can be
    flashed/displayed directly to the user

    ApiResponse class can hold any type of data in its data field.
    The actual type will be specified when an ApiResponse object is created

    Usage:
    @app.get("/endpoint", response_mode=ApiResponse[ResponseClass]
    return {"data":responseClass, "message":"retrival successful"}  # status defaults to 200

    # todo - for international translations, consider how this message can be translated as required
    """
    data: T|None = None  # generic data type to store any resonse data type.  Allow none for successful POST of data, etc
    message: str = "Operation Successful"  # Default message; can be overridden before sending response
    status_code: int = 200  # Default status; can be overridden before sending
