from typing import List
from sqlmodel import Field, SQLModel, Relationship

from app.models.role_permission_link import RolePermissionLink

class PermissionBase(SQLModel):

    permission_name: str = Field(max_length=255)
    permission_description: str = Field(max_length=255)

class Permission(PermissionBase, table=True):
    permission_id: int = Field(primary_key=True)
    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)

class PermissionRead(PermissionBase):
    permission_id: int