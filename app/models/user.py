#user.py

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, TIMESTAMP, text

from app.models.organisation import Organisation
from app.models.role import Role
from app.models.title import Title
from app.models.role import RoleRead


class UserBase(SQLModel):

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

    organisation_id: int = Field(foreign_key="organisation.organisation_id")


class User(UserBase, table=True):
    cognito_sub_id: str = Field(
        primary_key=True,
        max_length=255,
        description="cognito user pool subject ID - use as unique user ID",
    )
    __tablename__ = "user"


    title: Optional["Title"] = Relationship(back_populates="users")
    role: Optional["Role"] = Relationship(back_populates="users")
    organisation: Optional[Organisation] = Relationship(back_populates="users")

class UserReadProfile(UserBase):
    # todo - consider which elements to import, and which relationships to include, and how.
    # todo - may want different userRead functions for different purposes to minimise unnecessary data transfer
    pass

class UserReadSystem(UserBase):
    """
    For use by API only - not to be passed back to user/front end.
    Contains system data such as permissions lists for validating RBAC

    """
    cognito_sub_id: str
    role: Optional[RoleRead] = None
