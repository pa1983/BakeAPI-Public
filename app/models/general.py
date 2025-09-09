from datetime import datetime

from pydantic import BaseModel


class updateDataModel(BaseModel):
    field_name: str
    new_value: str | int | float | datetime | None | bool