import decimal
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlmodel import SQLModel, Relationship, Field

from app.database.session import engine
from app.models.currency import Currency
from app.models.image import Image, ImageRead, ImageInvoiceRead
from app.models.organisation import Organisation, OrganisationRead
# these otherwise unused imports are required to fulfill forward reference requirements of referenced models - without these mapper initialisation will fail
from app.models.role import Role
from app.models.ingredient import Ingredient
from app.models.supplier import Supplier
from app.models.user import User
from app.models.uom import UnitOfMeasure

class InvoiceStatus(SQLModel, table=True):
    """
    List of invoice stati to describe current invoice status
    """
    name: str = Field(primary_key=True)
    display_name: str = Field(nullable=False)
    description: str = Field()
    sort_order: int = Field(default=0)

class ParsedLineItem(SQLModel):
    """
    Definition of invoice line item fields to be extracted by Gemini - fed into gemini to form the output schema
    """

    cases: Optional[int] = Field(None, description="Number of cases for the line item - synonyms: cartons, boxes.")
    units: Optional[int] = Field(None, description="Number of units for the line item - synonyms: pieces.")
    description: str = Field(..., description="Description of the product or service. synonyms: title, desc, name")
    size: Optional[str] = Field(None, description="Size or dimensions of the item. synonyms: pack size")
    code: Optional[str] = Field(None, description="Product or item code. synonyms: sku, catalogue number")
    value_ex_vat: float = Field(..., description="Value of the line item excluding VAT to 2 decimal places.")
    value_inc_vat: float = Field(..., description="Value of the line item including VAT to 2 decimal places.")
    vat_percentage: float = Field(..., description="VAT percentage as a float (e.g., 0.20 for 20%).")
    is_delivery: bool = Field(False, description="Whether the line item is delivery.")


class ParsedInvoiceDetails(SQLModel):
    """
    Definition of invoice meta fields to be extracted from the invoice by Gemini
    Only fields to be extracted directly from the invoice by Gemini are included here.
    Inclusion of extaneous fields, such as parsing time and token usage, would cause an increase in gemini token usage
    and runtime as the AI engine would look for these data in the parsed invoice
    """
    supplier_name: Optional[str] = Field(None, description="Name of the supplier.")

    customer_account_number: Optional[str] = Field(None, alias="customer account number",
                                                   description="Customer's account number.")
    invoice_number: Optional[str] = Field(..., alias="invoice number", description="Invoice number. synonyms: invoice ID")
    user_reference: Optional[str] = Field(None, alias="user reference", description="User's reference on the invoice.")
    supplier_reference: Optional[str] = Field(None, alias="supplier reference",
                                              description="Supplier's reference on the invoice.")
    calculated_total: Optional[float] = Field(...,
                                    description="Sum of the total of all line items, taking into account the VAT rate for each line. This should be calculated from the extracted line items.")
    invoice_total: Optional[float] = Field(..., alias="invoice_total",
                                 description="The total invoice amount including VAT, as displayed on the invoice.")
    delivery_cost: Optional[float] = Field(..., alias="delivery_cost",
                                 description="This may appear as a line item on the invoice with a carrier name such as DPD, royal mail, fed ex, ups or other delivery providers.Total delivery cost. Default to 0.0 if not found on invoice")
    parsed_currency: Optional[str] = Field(..., alias="currency", description="Currency in 3-character ISO 4217 code.")
    document_type: str = Field("invoice",
                               description="Type of duocument, e.g. invoice, packing_list, order_confirmation,receipt")
    invoice_date: Optional[datetime] = Field(description="Date on which the invoice was created - must be converted to ISO date format.")
    confidence_score: float = Field(default=0, alias="confidence_score",
                                    description="Confidence score from Gemini of confidence in accuracy of parsing of the invoice.")


class ParsedInvoice(SQLModel):
    """
    container to allow for easy population of all data returned by gemini into model classes - will later be
    flattened before pushing to database tables
    """

    line_items: List[ParsedLineItem]
    invoice_details: ParsedInvoiceDetails



# new DTO model to handle parsed invoice data prior to updating into the existing invoice entry in the DB
class InvoiceUpdatePayload(SQLModel):
    invoice_details: ParsedInvoiceDetails
    line_items: List[ParsedLineItem]
    parse_duration_ms: int
    parse_ai_tokens: int
    currency_code: str|None  # gemini will pull currency name, at this point we're trying to match currency to a currency code
    supplier_id: int|None  # as above


class Invoice(ParsedInvoiceDetails, SQLModel, table=True):
    """
    Final table, including additional system-generated meta fields, to be saved the the database
    """
    id: Optional[int] = Field(primary_key=True, description="Invoice ID")
    date_added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    organisation_id: int = Field(None, description="Organisation ID of the invoice owner.",
                                           foreign_key="organisation.organisation_id")
    organisation: Optional[Organisation] = Relationship()
    date_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    parse_duration_ms: int = Field(default=0, alias="parse_duration_ms",
                                   description="Parser runtime duration in milliseconds.")
    parse_ai_tokens: int = Field(default=0, alias="parse_ai_tokens",
                                 description="Number of gemini tokens consumed by the parsing of this invoice - may be useful for customer billing/identification of system abuse.")
    currency_code: str|None = Field(default="GBP", foreign_key='currency.currency_code', alias="currency_code", description="Currency code as found on the invoice. Defaults to GBP initially as most users' invoices will be GBP")
    invoice_currency: Optional[Currency] = Relationship()
    supplier_id: int|None = Field(default=None, foreign_key='supplier.supplier_id', description="Supplier ID of the invoice owner.  Parser attempts to infer the ID from the supplier name string found on the invoice, but default is none if a match is not found.")

    status: str = Field(default='processing', foreign_key="invoicestatus.name")
    invoice_status: InvoiceStatus = Relationship()
    received_date: Optional[datetime] = Field(default=None, description="Date on which the physical order was received.")
    notes: Optional[str] = Field(description="Additional notes about the invoice or discrepancies within it")
    image_id: Optional[int] = Field(
        default=None,
        foreign_key="image.image_id",
        sa_column_kwargs={"unique": True},
        description="Invoice image ID - reference to the image table which contains the S3 data for the uploaded invoice file")
    # define the one-way relationship to the image table - no need for backpopulates as will never need to reference

    invoice_image: Optional[Image] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    # two-way relationship to line item as there may be need to access invoice from line item and vice-versa

    line_items: List['LineItem'] = Relationship(
        back_populates='invoice',
        sa_relationship_kwargs={"cascade": "save-update, merge, delete, delete-orphan"}
    )

    supplier: Optional[Supplier] = Relationship()  # todo - any need for a 2 way relationship here?

class LineItem(ParsedLineItem, SQLModel, table=True):
    """
    Extends ParsedLineItem, to take the parsed data and add links to the parent invoice ID, line item ID etc
    """
    __tablename__ = 'lineitem'
    id: Optional[int] = Field(primary_key=True, description="Line item ID", default=None)
    invoice_id: Optional[int] = Field(default=None, description='Reference to parent invoice ID', foreign_key="invoice.id")
    invoice: Optional[Invoice] = Relationship(back_populates="line_items")
    buyable_id: Optional[int] = Field(default=None, foreign_key="buyable.id") # these 3 fields are what downstream queries will use for costing calculations so need to be complete and accurate
    buyable_quantity: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=3)
    unit_cost: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=3)
    organisation_id: Optional[int] = Field(default=None, foreign_key="organisation.organisation_id")

class LineItemBase(SQLModel):
    invoice_id: Optional[int] = None
    cases: Optional[int] = None
    units: Optional[int] = None
    description: str
    size: Optional[str] = None
    code: Optional[str] = None
    value_ex_vat: float
    value_inc_vat: float
    vat_percentage: float
    is_delivery: bool = False
    buyable_id: Optional[int] = None
    buyable_quantity: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None

class LineItemCreate(LineItemBase):
    pass


class LineItemRead(LineItemBase):
    id: int

class LineItemUpdate(SQLModel):
    cases: Optional[int] = None
    units: Optional[int] = None
    description: Optional[str] = None
    size: Optional[str] = None
    code: Optional[str] = None
    value_ex_vat: Optional[float] = None
    value_inc_vat: Optional[float] = None
    vat_percentage: Optional[float] = None
    is_delivery: Optional[bool] = None
    buyable_id: Optional[int] = None
    buyable_quantity: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None


class InvoiceListResponse(SQLModel):
    """
    Used for calls to invoice/invoices endpoint to display list of invoices
    """

    id: int
    date_added: datetime
    date_modified: datetime
    supplier_name: str|None
    invoice_number: str|None
    status: InvoiceStatus
    image: Image

class InvoiceRead(ParsedInvoiceDetails):
    id: int
    date_added: Optional[datetime]
    date_modified: Optional[datetime]
    parse_duration_ms: Optional[int]
    parse_ai_tokens: Optional[int]
    received_date: Optional[datetime]
    currency_code: Optional[str]
    notes: Optional[str]
    supplier_id: Optional[int]
    # Nested "Read" models for relationships
    invoice_status: Optional[InvoiceStatus]
    invoice_image: Optional[ImageInvoiceRead]
    line_items: List[LineItemRead] = []


if __name__ == '__main__':
    engine = engine
    SQLModel.metadata.create_all(engine)
    pass