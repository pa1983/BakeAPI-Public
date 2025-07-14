# image.py
from datetime import datetime, timezone
from typing import Optional, List

from pydantic import ConfigDict, computed_field
from sqlmodel import SQLModel, Field, Relationship

from app.core.config import settings

S3_BASE_URL = settings.S3_BASE_URL

class ImageBase(SQLModel):  # common elements that will be used in both the table model and read model
    """
    Called ImageBase , but can be used for any documents being uploaded to S3
    """
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

    # @computed_field(property_name="image_url", return_schema={"type": "string"})
    # @property
    # def image_url(self) -> str:
    #     """
    #     Dynamically constructs the full image URL using the base S3 URL and the s3_key.
    #     """
    #     print('attempting to generate url')
    #     return f'{S3_BASE_URL}/{self.s3_key}'


class Image(ImageBase, table=True):  # inherit the image base
    """
    Represents an image entry in the database.
    Stores metadata about an image, its path, and who uploaded it.
    """
    image_id: Optional[int] = Field(default=None, primary_key=True)

    # define relationships to the TABLE as these can't be defined within the Base class
    organisation: Optional["Organisation"] = Relationship(back_populates="images")
    # REMOVED THIS to make a one-way relationship from ingredient to allow use of Image table by invoice etc define relationship to the IngredientImage linking table
    # ingredient_links: List["Ingredient_Image"] = Relationship(back_populates="image")
    # todo - add links to other tables, e.g. invoices, pricelists etc


class ImageRead(ImageBase):
    """
    Pydantic model for exposing Image data in API responses.
        Contains all API user-friendly data, excluding the relationship objects
        """
    image_id: int
    tst: str = "SAMPLE"  # <- this makes it into the API respponse, but the @property key and value do not appear
    model_config = ConfigDict(from_attributes=True)

    @computed_field(alias="image_url")
    @property
    def image_url(self) -> str:
        """
        Dynamically constructs the full image URL using the base S3 URL and the s3_key.
        """
        print('attempting to generate url')
        return f'{S3_BASE_URL}/{self.s3_key}'
