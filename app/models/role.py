from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship

from app.models.permission import PermissionRead
from app.models.role_permission_link import RolePermissionLink


class RoleBase(SQLModel):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")


class Role(RoleBase, table=True):
    organisation: Optional["Organisation"] = Relationship(back_populates="roles")
    users: List["User"] = Relationship(back_populates="role")
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermissionLink
    )

class RoleRead(RoleBase):
    role_id: int
    permissions: List[PermissionRead] = []
