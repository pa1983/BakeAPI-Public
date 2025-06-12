# from __future__ import annotations # Removed this line


from sqlmodel import Field, Relationship, Column, TIMESTAMP, text, SQLModel

from typing import Optional, List
from datetime import datetime, timezone


class Organisation(SQLModel, table=True):
    organisation_id: Optional[int] = Field(default=None, primary_key=True)
    organisation_name: str = Field(max_length=255)

    # Type hints are now string literals for forward references
    roles: List["Role"] = Relationship(back_populates="organisation")
    ingredients: List["Ingredient"] = Relationship(back_populates="organisation")
    images: List["Image"] = Relationship(back_populates="organisation")

class OrganisationRead(SQLModel):
    organisation_id: int
    organisation_name: str


class unit_of_measure(SQLModel, table=True):
    uom_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=50)
    abbreviation: str = Field(index=True, unique=True, max_length=10)
    type: str = Field(max_length=20)
    conversion_factor: float = Field(ge=0)
    is_base_unit: bool

    # Type hints are now string literals for forward references
    ingredients: List["Ingredient"] = Relationship(
        back_populates="standard_uom"
    )

    class Config:
        pass


class Ingredient_Image(SQLModel, table=True):
    """
    Linking table for the many-to-many relationship between Ingredient and Image.
    """
    ingredient_id: int = Field(
        foreign_key="ingredient.ingredient_id", primary_key=True,
        description="Foreign key to the Ingredient table."
    )
    image_id: int = Field(
        foreign_key="image.image_id", primary_key=True,
        description="Foreign key to the Image table."
    )

    sort_order: Optional[int] = Field(
        default=10,
        description='Used to predefine sort order for display purposes.'
    )

    ingredient: "Ingredient" = Relationship(back_populates="image_links")
    image: "Image" = Relationship(back_populates="ingredient_links")


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = "role_permission"
    role_id: Optional[int] = Field(
        default=None, foreign_key="role.role_id", primary_key=True
    )
    permission_id: Optional[int] = Field(
        default=None, foreign_key="permission.permission_id", primary_key=True
    )


class Role(SQLModel, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    organisation_id: Optional[int] = Field(
        default=None, foreign_key="organisation.organisation_id"
    )
    organisation: Optional[Organisation] = Relationship(back_populates="roles")
    # Type hints are now string literals for forward references
    users: List["User"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermissionLink
    )


class Permission(SQLModel, table=True):
    permission_id: int = Field(primary_key=True)
    permission_name: str = Field(max_length=255)
    permission_description: str = Field(max_length=255)
    # Type hints are now string literals for forward references
    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)


class Title(SQLModel, table=True):
    short_title: str = Field(primary_key=True, max_length=255)
    full_title: str = Field(max_length=255)
    notes: Optional[str] = Field(
        default=None, max_length=255, description="explanation of meaning of title")
    sort_order: int = Field(default=10)

    # Type hints are now string literals for forward references
    users: List["User"] = Relationship(back_populates="title")


class User(SQLModel, table=True):
    __tablename__ = "user"

    cognito_sub_id: str = Field(
        primary_key=True,
        max_length=255,
        description="cognito user pool subject ID - use as unique user ID",
    )
    email_address: str = Field(
        max_length=255,
        unique=True,
        description="max address per RFC 5321 is 254 chars",
    )
    forename: str = Field(max_length=255)
    surname: Optional[str] = Field(
        default=None,
        max_length=255,
        description="nullable to allow for users from regions that dont use both fore and surnames",
    )
    short_title: str = Field(
        max_length=255, foreign_key="title.short_title"
    )
    phone: str = Field(
        max_length=255, description="required as means of communicating with users"
    )
    preferences: Optional[str] = Field(
        default=None,
        max_length=4000,
        description="for developer use to store preferences and miscellaneous user data",
    )
    email_validated_datetime: Optional[datetime] = Field(default=None)
    role_id: int = Field(
        foreign_key="role.role_id",
        index=True
    )

    created_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    modified_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP, nullable=False,
                         server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    title: Optional[Title] = Relationship(back_populates="users")
    role: Optional[Role] = Relationship(back_populates="users")

    organisation_id: int = Field(foreign_key="organisation.organisation_id")


class Ingredient(SQLModel, table=True):
    ingredient_id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_name: str = Field(max_length=50, unique=True, index=True)
    standard_uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    density: Optional[float] = Field(default=None)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")

    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                        nullable=False)
    modified_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                         sa_column_kwargs={"onupdate": "NOW()"})

    standard_uom: unit_of_measure = Relationship(back_populates="ingredients")
    organisation: Optional[Organisation] = Relationship(back_populates="ingredients")

    # Type hints are now string literals for forward references
    image_links: List["Ingredient_Image"] = Relationship(
        back_populates="ingredient"
    )


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

    organisation: Optional[Organisation] = Relationship(back_populates="images")

    # Type hints are now string literals for forward references
    ingredient_links: List['Ingredient_Image'] = Relationship(
        back_populates="image"
    )


class ImageRead(SQLModel):
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


class IngredientRead(SQLModel):
    ingredient_id: int
    ingredient_name: str
    standard_uom_id: int
    density: Optional[float]
    organisation_id: Optional[int]
    created_timestamp: datetime
    modified_timestamp: datetime

    standard_uom: unit_of_measure
    organisation: Optional[OrganisationRead]

    images: List["ImageRead"] = [] # This is for Pydantic serialization, not a SQLModel relationship directly


# Call update_forward_refs() after all models are defined
SQLModel.model_rebuild()
