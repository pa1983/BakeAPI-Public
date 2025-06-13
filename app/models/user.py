#user.py

# from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, TIMESTAMP, text

from app.models.organisation import Organisation


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = "role_permission"  # Explicitly set table name for the link table
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
    users: List["User"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermissionLink
    )


class Permission(SQLModel, table=True):
    permission_id: int = Field(primary_key=True)
    permission_name: str = Field(max_length=255)
    permission_description: str = Field(max_length=255)
    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)


class Title(SQLModel, table=True):
    short_title: str = Field(primary_key=True, max_length=255)
    full_title: str = Field(max_length=255)
    notes: Optional[str] = Field(
        default=None, max_length=255, description="explanation of meaning of title")
    sort_order: int = Field(default=10)

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
