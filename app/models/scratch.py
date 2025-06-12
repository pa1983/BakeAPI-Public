# from __future__ import annotations


from sqlmodel import Field, Relationship, Column, TIMESTAMP, text, select, SQLModel
from app.database.session import Session, engine
from sqlalchemy.orm import Mapped
from typing import Optional, List
from datetime import datetime, timezone


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Role, Ingredient, Image



class Organisation(SQLModel, table=True):
    organisation_id: Optional[int] = Field(default=None, primary_key=True)
    organisation_name: str = Field(max_length=255)

    roles: Mapped[List["Role"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})
    ingredients: Mapped[List["Ingredient"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})
    images: Mapped[List["Image"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})


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

    ingredients: Mapped[List["Ingredient"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})





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

# These relationships are defined *after* the class because they refer to other classes
# Using lambda for Relationship

IngredientImage.ingredient: Mapped["Ingredient"] = Relationship(back_populates="image_links")
IngredientImage.image: Mapped["Image"] = Relationship(back_populates="ingredient_links")


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
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")

    organisation: Mapped[Optional["Organisation"]] = Relationship(back_populates="roles")
    users: Mapped[List["User"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})
    permissions: Mapped[List["Permission"]] = Relationship(
        sa_relationship_kwargs={"lazy": "raise_on_sql"}, link_model=RolePermissionLink
    )


class Permission(SQLModel, table=True):
    permission_id: int = Field(primary_key=True)
    permission_name: str = Field(max_length=255)
    permission_description: str = Field(max_length=255)

    roles: Mapped[List["Role"]] = Relationship(
        sa_relationship_kwargs={"lazy": "raise_on_sql"},
        link_model=RolePermissionLink
    )





class Title(SQLModel, table=True):
    short_title: str = Field(primary_key=True, max_length=255)
    full_title: str = Field(max_length=255)
    notes: Optional[str] = Field(default=None, max_length=255)
    sort_order: int = Field(default=10)

    users: Mapped[List["User"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})



class User(SQLModel, table=True):
    __tablename__ = "user"

    cognito_sub_id: str = Field(primary_key=True, max_length=255)
    email_address: str = Field(max_length=255, unique=True)
    forename: str = Field(max_length=255)
    surname: Optional[str] = Field(default=None, max_length=255)
    short_title: str = Field(max_length=255, foreign_key="title.short_title")
    phone: str = Field(max_length=255)
    preferences: Optional[str] = Field(default=None, max_length=4000)
    email_validated_datetime: Optional[datetime] = Field(default=None)
    role_id: int = Field(foreign_key="role.role_id", index=True)
    organisation_id: int = Field(foreign_key="organisation.organisation_id")

    created_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    modified_timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP, nullable=False,
                         server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
    )

    title: Mapped[Optional["Title"]] = Relationship(back_populates="users")
    role: Mapped[Optional["Role"]] = Relationship(back_populates="users")


class Ingredient(SQLModel, table=True):
    ingredient_id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_name: str = Field(max_length=50, unique=True, index=True)
    standard_uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    density: Optional[float] = Field(default=None)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")

    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    modified_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                         sa_column_kwargs={"onupdate": "NOW()"})

    standard_uom: Mapped["unit_of_measure"] = Relationship(back_populates="ingredients")
    organisation: Mapped[Optional["Organisation"]] = Relationship(back_populates="ingredients")
    image_links: Mapped[List["IngredientImage"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})


class Image(SQLModel, table=True):
    image_id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str = Field(max_length=255, nullable=False)
    file_ext: str = Field(max_length=10, nullable=False)
    mime_type: str = Field(max_length=50, nullable=False)
    file_size: int = Field(nullable=False)
    alt_text: Optional[str] = Field(default=None, max_length=500)
    caption: Optional[str] = Field(default=None, max_length=1000)

    created_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    modified_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": "NOW()"},
        nullable=True,
    )

    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")
    s3_key: str = Field(max_length=255, nullable=False)

    organisation: Mapped[Optional["Organisation"]] = Relationship(back_populates="images")
    ingredient_links: Mapped[List["IngredientImage"]] = Relationship(sa_relationship_kwargs={"lazy": "raise_on_sql"})



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

    images: List["ImageRead"] = []






with Session(engine) as session:
    statement = (
        select(Ingredient, IngredientImage)
        .join(IngredientImage)
        .join(Image)

    )
    results = session.exec(statement).all()
    print(results)