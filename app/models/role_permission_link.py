from typing import Optional

from sqlmodel import SQLModel, Field


class RolePermissionLink(SQLModel, table=True):
    __tablename__ = "role_permission"  # Explicitly set table name for the link table
    role_id: Optional[int] = Field(
        default=None, foreign_key="role.role_id", primary_key=True
    )
    permission_id: Optional[int] = Field(
        default=None, foreign_key="permission.permission_id", primary_key=True
    )
