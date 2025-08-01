import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship, Column, TIMESTAMP
from sqlalchemy.sql import func


class BuyableBase(SQLModel):
    """
    Contains all the common fields shared between create, update, and read models.
    """
    sku: str = Field(
        max_length=255,
        description="Manufacturer SKU for the product."
    )
    item_name: str = Field(
        max_length=255,
        description="The name of the item, as supplied by the manufacturer."
    )
    quantity: Decimal = Field(
        max_digits=18,
        decimal_places=10,
        description="Quantity of item, in UOM units, per SKU pack."
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000
    )
    is_active: bool = Field(default=True)

    # Foreign Key fields
    brand_id: Optional[int] = Field(default=None, foreign_key="brand.brand_id")
    uom_id: int = Field(foreign_key="unit_of_measure.uom_id")
    organisation_id: int = Field(foreign_key="organisation.organisation_id")


class Buyable(BuyableBase, table=True):
    __tablename__ = "buyable"
    # field contents managed by the database

    id: Optional[int] = Field(default=None, primary_key=True)

    created_timestamp: datetime.datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now()
        ),
        default_factory= datetime.datetime.now(datetime.UTC),
    )
    modified_timestamp: datetime.datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now()
        ),
        default_factory= datetime.datetime.now(datetime.UTC),
    )

    # --- Relationships
    brand: Optional["Brand"] = Relationship(back_populates="buyables")
    unit_of_measure: "UnitOfMeasure" = Relationship()
    organisation: "Organisation" = Relationship()


class BuyableRead(BuyableBase):

    id: int
    created_timestamp: datetime.datetime
    modified_timestamp: datetime.datetime

