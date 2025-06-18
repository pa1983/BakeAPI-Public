from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class Title(SQLModel, table=True):
    short_title: str = Field(primary_key=True, max_length=255)
    full_title: str = Field(max_length=255)
    notes: Optional[str] = Field(
        default=None, max_length=255, description="explanation of meaning of title")
    sort_order: int = Field(default=10)

    users: List["User"] = Relationship(back_populates="title")