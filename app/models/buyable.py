import typing
from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import func, UniqueConstraint

from app.models.brand import Brand
from app.models.organisation import Organisation
from app.models.uom import UnitOfMeasure


# Base model: Contains all fields that are shared and can be provided by a user during creation/update.
# It does not include auto-generated fields like id, timestamps, or organisation_id (awt from user's session data for security).
class BuyableBase(SQLModel):
    brand_id: typing.Optional[int] = Field(default=None, foreign_key="brand.brand_id")
    sku: str = Field(max_length=255)
    item_name: str = Field(max_length=255)
    uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    quantity: Decimal = Field(max_digits=18, decimal_places=10)
    is_active: bool = Field(default=True)
    notes: typing.Optional[str] = Field(default=None, max_length=1000)


class Buyable(BuyableBase, table=True):
    id: typing.Optional[int] = Field(default=None, primary_key=True)
    organisation_id: int = Field(foreign_key="organisation.id")

    created_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                        nullable=False)
    modified_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                         nullable=False,
                                         sa_column_kwargs={"onupdate": func.now()})  # need to call sqlalchmeny now here or won't update as expected

    # --- Relationships ---  These should ensure that API DB updates fail if incorrect IDs are passed by user
    brand: "Brand" = Relationship(back_populates="buyables")  # back populates to allow for cascading deletion of buyables if a brand is deleted.
    uom: "UnitOfMeasure" = Relationship()
    organisation: "Organisation" = Relationship()

    # Unique Constraint - same SKU cannot be duplicated within one organisation
    __table_args__ = (
        UniqueConstraint("sku", "organisation_id", name="buyable_sky_org_pk")
    )


# Read model: Defines the shape of the data when it's returned from the API.
# It includes the auto-generated fields that should be visible to the client.
class BuyableRead(BuyableBase):
    id: int
    created_timestamp: datetime
    modified_timestamp: datetime