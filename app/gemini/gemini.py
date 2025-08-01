import json
import pathlib
import time

from google import genai
from google.genai.types import Tool, FunctionDeclaration, Part, GenerationConfig
from sqlmodel import select

from app.core.logging_config import logger
from app.database.session import db_session
from app.gemini import sample_data
from app.gemini.schema import GEMINI_SCHEMA
from app.core.config import settings
from app.models.invoice import ParsedInvoice, Invoice, LineItem, InvoiceUpdatePayload, Currency
from app.models.supplier import Supplier

from app.services.s3_handler import delete_s3_object

client = genai.Client(api_key=settings.GEMINI_API_KEY)

TEST = True

PROMPT_INSTRUCTIONS = """
parse this invoice, using the descriptions of fields in the schema for guidance. 
If you can't find exact matches look for something similar. 
Attempt to convert any vat codes to actual vat percentages and present as a floating point number
- code tables should be available in the document.
Dates MUST be converted to ISO date time format, or left null.
Provide a confidence score based on your confidence in the accuracy of the parsed data (floating point number from 0 to 1).
"""

GENERATION_CONFIG: dict = {
    "max_output_tokens": 20000,
    "response_mime_type": "application/json",
    "response_schema": GEMINI_SCHEMA,

}

MODEL = "gemini-2.5-flash-lite-preview-06-17"  # how will this change over time to match the current preview version?  need to call ListModels and find current relevant model

# Define the tool during instantiation, then reuse in subsequent calls
invoice_parser_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="extract_invoice_data",  # name for the tool
            description="Extracts data from invoice as per the provided schema",
            # description of the tool # todo - in future could allow individual users to alter their parsing requirements
            parameters=GEMINI_SCHEMA
            # Defines fields and datatypes to be extracted only changes if change the fields to be pulled from invoices
        )
    ]
)


def send_invoice_to_gemini(pdf_file_data_bytes: bytes):
    """
    Send invoice PDF or image to Gemini for parsing.
    A strict schema that matches the Pydantic model, which in turn matches the database SQLModel file, is also
    sent to ensure the response is received in the correct format.  This also helps inform Gemini's parser.
    :return:
    """

    prompt_parts = [
        PROMPT_INSTRUCTIONS,  # fixed - always stays the same
        Part.from_bytes(
            mime_type="application/pdf",
            data=pdf_file_data_bytes
        )
    ]

    try:
        logger.info(f"Sending invoice to Gemini for parsing")
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt_parts,
            config=GENERATION_CONFIG
        )
        logger.info(f'Gemini response received. total token usage: {response.usage_metadata.total_token_count} - cost = ${0.4 / 1000000 * response.usage_metadata.total_token_count}. INVOICES PROCESSABLE PER usd = {1 / (0.4 / 1000000 * response.usage_metadata.total_token_count)}')
        return response

    except Exception as e:
        logger.error(e)
        # there's no good way out - raise the exception to break the process
        raise e


def extract_gemini_response(gemini_response):
    # Process the response
    try:
        extracted_data = json.loads(gemini_response.text)
        logger.debug("Successfully extracted invoice data from gemini response")
        # attempt to populate a ParsedInvoice instance from the extracted json data. This is a container class
        # containing both the invoice metadata and the parsed line items list
        parsed_invoice = ParsedInvoice(**extracted_data)
        return parsed_invoice  #

    except (json.JSONDecodeError, AttributeError, IndexError) as e:
        logger.exception(f"Could not extract or parse JSON data - looks like an error in Gemini's output - invalid JSON-  Error: {e}")
        raise e
        try:
            logger.exception("gemini_response.text:  ", gemini_response.text)
        except Exception:
            logger.exception("Could not get gemini_response.text")


def apply_db_schema_to_response_data(parsed_invoice: ParsedInvoice, invoice_id:int, organisation_id: int, runtime_ms: int|float, tokens_used: int) -> Invoice:
    try:  # todo - get these data from the user's token data
        metadata = {
            "organisation_id": organisation_id,
            "parse_duration_ms": runtime_ms,
            "parse_ai_tokens": tokens_used,
            "id": invoice_id
        }

        # take the parsed invoice and convert it to a DB invoice model, adding in the additional metadata
        invoice_to_save = Invoice(
            **parsed_invoice.invoice_details.model_dump(),
            **metadata
        )
        # split out the line items into a list
        line_items_to_save = [
            LineItem(**item.model_dump()) for item in parsed_invoice.line_items
        ]
        invoice_to_save.line_items = line_items_to_save

        return invoice_to_save
    except Exception as e:
        logger.exception(f'error in apply_db_schema_to_response_data: {e}')
        raise e


# def push_invoice_to_db(invoice_to_save: Invoice) -> Invoice:
#     try:
#         with db_session() as session:
#             # get the existing invoice instance by ID
#             existing_invoice = session.exec(select(Invoice).where(Invoice.id == invoice_to_save.id)).first()
#
#             for attr in [i for i in Invoice.model_fields if i != 'id']:
#
#                 val = getattr(invoice_to_save, attr)
#                 if val:
#                     # checking that val is not null prevents overwriting existing data by excluding fields set to None
#                     setattr(existing_invoice, attr, val)
#
#             existing_invoice.status = 'draft'  # mark the updated invoice as status==draft (was processing)
#             existing_invoice.line_items = invoice_to_save.line_items
#             session.add(existing_invoice)
#             session.commit()
#             session.refresh(existing_invoice)
#             return existing_invoice
#     except Exception as e:
#         logger.exception(f"Could not push invoice to database. Error: {e}--{existing_invoice}")
#         raise e


def push_invoice_to_db(payload: InvoiceUpdatePayload, invoice_id: int) -> Invoice:
    """
    Updates an existing invoice in the database with parsed data.
    This function replaces all existing line items with the new ones.
    """
    try:
        with db_session() as session:
            # Get the existing invoice instance by ID
            existing_invoice = session.get(Invoice, invoice_id)
            if not existing_invoice:
                raise ValueError(f"Invoice with ID {invoice_id} not found.")

            # 1. Update the scalar fields on the Invoice object
            # This is a cleaner way to get only the fields that were set in the source object.
            # update_data = invoice_to_save.model_dump(exclude_unset=True, exclude={'id', 'line_items'})
            update_data = payload.invoice_details.model_dump(exclude_unset=True, exclude={'id'})
            update_data['parse_duration_ms'] = payload.parse_duration_ms
            update_data['parse_ai_tokens'] = payload.parse_ai_tokens
            update_data['supplier_id'] = payload.supplier_id
            update_data['currency_code'] = payload.currency_code

            for key, value in update_data.items():

                if value is not None:
                    setattr(existing_invoice, key, value)


            # Explicitly delete each old line item from the session
            for old_item in existing_invoice.line_items:
                # there are unlikely to be aby old line items to delete, but delete in case to avoid potential duplication if an invoice were to be parsed twice
                session.delete(old_item)

            # Flush the session to send the DELETE statements to the DB transaction
            # before adding the new items. This avoids potential conflicts.
            session.flush()

            # Now, assign the new line items. SQLAlchemy will see these as new
            # objects to be added to the database and linked to the invoice.
            new_line_items = [LineItem(**item.model_dump()) for item in payload.line_items]
            existing_invoice.line_items = new_line_items

            # 3. Update status and commit all changes
            existing_invoice.status = 'draft'
            # session.add(existing_invoice)
            session.commit()
            session.refresh(existing_invoice)
            return existing_invoice

    except Exception as e:
        # Log the incoming object as the local variable might not be set if an error occurs early
        logger.exception(f"Could not push invoice to database. Error: {e} -- Data: {payload.model_dump_json()}")
        raise e


def set_invoice_status_failed(invoice_id):
    try:
        with db_session() as session:
            invoice = session.exec(select(Invoice).where(Invoice.id == invoice_id)).first()
            invoice.status = 'failed'
            session.commit()
    except Exception as e:
        logger.debug(f'error deleting invoice {invoice_id}: {e}')


def infer_currency_code(currency: str) -> str | None:
    """
    Takes the currency string found on the invoice and attempts to match it to a currency_code in the currency table
    :param currency: currency string from database
    :return: currency_code from currency db table
    """
    if not currency:
        return None
    with db_session() as session:
        currency_code = session.exec(
            select(Currency.currency_code).where(Currency.currency_code == currency.strip().upper())
        ).first()
        return currency_code


def infer_supplier_id(supplier: str)-> int|None:
    # todo - improve this logic to allow for a fuzzy match
    if not supplier:
        return None
    with db_session() as session:
        supplier_id = session.exec(
            select(Supplier.supplier_id)
            .where(supplier.strip() == Supplier.supplier_name)
        ).first()

        return supplier_id


def parse_invoice(pdf_file_data_bytes: bytes, invoice_id, organisation_id) -> Invoice|None:
    try:
        parse_start_time = time.perf_counter()
        logger.info("invoice parser initiated")
        gemini_response = send_invoice_to_gemini(pdf_file_data_bytes)
        runtime_ms = (time.perf_counter() - parse_start_time) * 1000
        parsed_invoice: ParsedInvoice = extract_gemini_response(gemini_response)
        # infer linked table fields - currency_code, supplier_id, line item buyable id
        currency_code = infer_currency_code(parsed_invoice.invoice_details.parsed_currency)
        supplier_id = infer_supplier_id(parsed_invoice.invoice_details.supplier_name)

        update_payload = InvoiceUpdatePayload(
            invoice_details = parsed_invoice.invoice_details,
            line_items=parsed_invoice.line_items,
            parse_duration_ms = int(runtime_ms),
            parse_ai_tokens= gemini_response.usage_metadata.total_token_count,
            currency_code = currency_code,
            supplier_id = supplier_id
        )

        saved_invoice = push_invoice_to_db(payload=update_payload, invoice_id=invoice_id)
        return saved_invoice
    except Exception as e:
        logger.exception(f"Could not parse invoice. Error: {e}--{invoice_id}")
        set_invoice_status_failed(invoice_id=invoice_id)
        raise e



        # todo - if parse fails, mark the invoice as FAILED - invite user to retry

if __name__ == '__main__':
    # Read the PDF file's raw byte data.
    try:
        path_to_pdf = r"C:\Users\44784\Downloads\milk sample Invoice_E628-26309.pdf"
        pdf_file_data_bytes = pathlib.Path(path_to_pdf).read_bytes()
        parse_invoice(pdf_file_data_bytes, invoice_id=27, organisation_id=2)  # todo - add retry here - 3 times?  to allow for failed gemini response
    except FileNotFoundError:
        print(f"Error: The file was not found at {path_to_pdf}")
        exit()
