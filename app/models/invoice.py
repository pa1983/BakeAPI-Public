import json
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    cases: Optional[int] = Field(None, description="Number of cases for the line item - synonyms: cartons, boxes.")
    units: Optional[int] = Field(None, description="Number of units for the line item - synonyms: pieces.")
    description: str = Field(..., description="Description of the product or service. synonyms: title, desc, name")
    size: Optional[str] = Field(None, description="Size or dimensions of the item. synonyms: pack size")
    code: Optional[str] = Field(None, description="Product or item code. synonyms: sku, catalogue number")
    value_ex_vat: float = Field(..., description="Value of the line item excluding VAT to 2 decimal places.")
    value_inc_vat: float = Field(..., description="Value of the line item including VAT to 2 decimal places.")
    vat_percentage: float = Field(..., description="VAT percentage as a float (e.g., 0.20 for 20%).")
    is_delivery: bool = Field(False, description="Whether the line item is delivery.")

class InvoiceDetails(BaseModel):
    supplier_name: Optional[str] = Field(None, description="Name of the supplier.")
    supplier_id: Optional[int] = Field(None, description="Supplier_ID of the supplier if the parsing engine can find a patch to list of existing suppliers.")
    customer_account_number: Optional[str] = Field(None, alias="customer account number", description="Customer's account number.")
    invoice_number: str = Field(..., alias="invoice number", description="Invoice number. synonyms: invoice ID")
    user_reference: Optional[str] = Field(None, alias="user reference", description="User's reference on the invoice.")
    supplier_reference: Optional[str] = Field(None, alias="supplier reference", description="Supplier's reference on the invoice.")
    calculated_total: float = Field(..., description="Sum of the total of all line items, taking into account the VAT rate for each line. This should be calculated from the extracted line items.")
    invoice_total: float = Field(..., alias="invoice_total", description="The total invoice amount including VAT, as displayed on the invoice.")
    delivery_cost: float = Field(..., alias="delivery_cost", description="This may appear as a line item on the invoice with a carrier name such as DPD, royal mail, fed ex, ups or other delivery providers.Total delivery cost. Default to 0.0 if not found on invoice")
    currency: str = Field(..., alias="currency", description="Currency in 3-character ISO 4217 code.")
    document_type: str = Field("invoice", description="Type of duocument, e.g. invoice, packing_list, order_confirmation,receipt")
    invoice_date: date = Field(description="Date on which the invoice was created.")
    confidence_score: float = Field(..., alias="confidence_score", description="Confidence score from Gemini of confidence in accuracy of parsing of the invoice.")

class ParsedInvoice(BaseModel):
    line_items: List[LineItem]
    invoice_details: InvoiceDetails


# Parsed invoice can then be subclassed into a database element that will include additional fields, i.e.
#  organisation_id  - to tie the invoice to a specific organisation
#  date_added - datetime invoice was parsed
#  date_modified
#  s3 key - details of uploaded invoice item