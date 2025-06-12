# image.py

from __future__ import annotations # Postpone evaluation of type hints to prevent circular import issues

from datetime import datetime, timezone
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from app.models.organisation import Organisation


class Image(SQLModel, table=True):
    """
    Represents an image entry in the database.
    Stores metadata about an image, its path, and who uploaded it.
    """
    image_id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(max_length=255, nullable=False)
    file_ext: str = Field(max_length=10, nullable=False, description='File extension')
    mime_type: str = Field(max_length=50, nullable=False)
    file_size: int = Field(nullable=False)
    alt_text: Optional[str] = Field(default=None, max_length=500)
    caption: Optional[str] = Field(default=None, max_length=1000)

    created_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=True,
        description="Timestamp when the image record was created."
    )
    modified_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": "NOW()"},
        nullable=True,
        description="Timestamp when the image record was last modified."
    )

    organisation_id: Optional[int] = Field(
        default=None,
        foreign_key="organisation.organisation_id",
        description='Null if image is a generic system image'
    )

    s3_key: str = Field(
        max_length=255, nullable=False,
        description='Used as S3, or other cloud store, document key. UUID avoids need for checking if name already exists.'
    )



    # # Relationship to the IngredientImage linking table (assuming it still exists)
    # ingredients: List["Ingredient"] = Relationship( # Changed to direct type hint for Ingredient
    #     link_model="IngredientImage", # Use string literal for link_model too for safety
    #     back_populates="images"
    # )
    # define relationship to the IngredientImage linking table
    ingredient_links: List['IngredientImageLink'] = Relationship(back_populates="ingredient")



class ImageRead(SQLModel):
    """
    Pydantic model for exposing Image data in API responses.
    """
    image_id: int
    file_name: str
    file_ext: str
    mime_type: str
    file_size: int
    alt_text: Optional[str]
    caption: Optional[str]
    created_timestamp: datetime
    modified_timestamp: datetime
    organisation_id: Optional[int]
    s3_key: str



