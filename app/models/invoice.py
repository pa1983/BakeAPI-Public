import json
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Relationship, Field

from app.database.session import engine
from app.models.image import Image
from app.models.organisation import Organisation
# these otherwise unused imports are required to fulfill forward reference requirements of referenced models - without these mapper initialisation will fail
from app.models.role import Role
from app.models.ingredient import Ingredient
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
    supplier_id: Optional[int] = Field(None,
                                       description="Supplier_ID of the supplier if the parsing engine can find a patch to list of existing suppliers.")
    customer_account_number: Optional[str] = Field(None, alias="customer account number",
                                                   description="Customer's account number.")
    invoice_number: Optional[str] = Field(..., alias="invoice number", description="Invoice number. synonyms: invoice ID")
    user_reference: Optional[str] = Field(None, alias="user reference", description="User's reference on the invoice.")
    supplier_reference: Optional[str] = Field(None, alias="supplier reference",
                                              description="Supplier's reference on the invoice.")
    calculated_total: float|None = Field(...,
                                    description="Sum of the total of all line items, taking into account the VAT rate for each line. This should be calculated from the extracted line items.")
    invoice_total: float|None = Field(..., alias="invoice_total",
                                 description="The total invoice amount including VAT, as displayed on the invoice.")
    delivery_cost: float|None = Field(..., alias="delivery_cost",
                                 description="This may appear as a line item on the invoice with a carrier name such as DPD, royal mail, fed ex, ups or other delivery providers.Total delivery cost. Default to 0.0 if not found on invoice")
    currency: str = Field(..., alias="currency", description="Currency in 3-character ISO 4217 code.")
    document_type: str = Field("invoice",
                               description="Type of duocument, e.g. invoice, packing_list, order_confirmation,receipt")
    invoice_date: datetime = Field(description="Date on which the invoice was created.")
    confidence_score: float = Field(default=0, alias="confidence_score",
                                    description="Confidence score from Gemini of confidence in accuracy of parsing of the invoice.")


class ParsedInvoice(SQLModel):
    """
    container to allow for easy population of all data returned by gemini into model classes - will later be
    flattened before pushing to database tables
    """

    line_items: List[ParsedLineItem]
    invoice_details: ParsedInvoiceDetails


class Invoice(ParsedInvoiceDetails, SQLModel, table=True):
    """
    Final table, including additional system-generated meta fields, to be saved the the database
    """
    id: Optional[int] = Field(primary_key=True, description="Invoice ID")
    date_added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    organisation_id: Optional[int] = Field(None, description="Organisation ID of the invoice owner.",
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
    # the invoice from the image
    invoice_image: Optional[Image] = Relationship()
    # two-way relationship to line item as there may be need to access invoice from line item and vice-versa
    line_items: List['LineItem'] = Relationship(back_populates='invoice')

class DBInvoice(Invoice, SQLModel, table=True):


class LineItem(ParsedLineItem, SQLModel, table=True):
    """
    Extends ParsedLineItem, to take the parsed data and add links to the parent invoice ID, line item ID etc
    """
    id: Optional[int] = Field(primary_key=True, description="Line item ID")
    invoice_id: Optional[int] = Field(default=None, description='Reference to parent invoice ID', foreign_key="invoice.id")
    invoice: Optional[Invoice] = Relationship(back_populates="line_items")


class InvoiceListResponse(BaseModel):
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

if __name__ == '__main__':
    engine = engine
    SQLModel.metadata.create_all(engine)
    pass