import decimal
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel, Relationship

from app.models.currency import Currency

# todo- split this to base, db and read

class Supplier(SQLModel, table=True):
    """
    SQLModel class representing a supplier.
    """
    # Define __table_args__ for the unique constraint - only one instance of supplier_name per org id
    __table_args__ = (
        UniqueConstraint("supplier_name", "organisation_id", name="UQ_supplier_name_organisation_id"),
    )
    supplier_id: int = Field(default=None, primary_key=True)
    supplier_name: str = Field(max_length=255)
    account_number: Optional[str] = Field(default=None, max_length=255)
    contact_person: Optional[str] = Field(default=None, max_length=25)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    email_address: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=2550)
    currency_code: str = Field(foreign_key="currency.currency_code", max_length=5)
    minimum_order_value: Optional[decimal.Decimal] = Field(
        default=0.0, max_digits=18, decimal_places=10
    )
    delivery_charge: Optional[decimal.Decimal] = Field(
        default=0.0, max_digits=18, decimal_places=10
    )

    organisation_id: int = Field(foreign_key="organisation.organisation_id")
    currency: Optional[Currency] = Relationship()

    image_id: Optional[int] = Field(default=None, nullable=True, foreign_key="image.image_id")