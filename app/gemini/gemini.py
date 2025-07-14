import json
import pathlib
import time

from google import genai
from google.genai.types import Tool, FunctionDeclaration, Part

from app.gemini import sample_data
from schema import GEMINI_SCHEMA
from app.core.config import settings
from app.models.invoice import ParsedInvoice, Invoice, LineItem

client = genai.Client(api_key=settings.GEMINI_API_KEY)

TEST = True

PROMPT_INSTRUCTIONS = """
parse this invoice, using the descriptions of fields in the schema for guidance. 
If you can't find exact matches look for something similar. 
Attempt to convert any vat codes to actual vat percentages and present as a floating point number
- code tables should be available in the document.
"""

MODEL = "gemini-2.5-flash-lite-preview-06-17"  # how will this change over time to match the current preview version?  need to call ListModels and find current relevant model

path_to_pdf = r"C:\Users\44784\Downloads\sysco SalesInvoice-Report.pdf"

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

# 1. Read the PDF file's raw byte data.
try:
    print(f"Reading file: {path_to_pdf}...")
    pdf_file_data = pathlib.Path(path_to_pdf).read_bytes()
except FileNotFoundError:
    print(f"Error: The file was not found at {path_to_pdf}")
    exit()

# 2. Construct the prompt parts.
prompt_parts = [
    PROMPT_INSTRUCTIONS,  # fixe - always stays the same
    Part.from_bytes(
        mime_type="application/pdf",
        data=pdf_file_data
    )
]

generation_config = {
    "response_mime_type": "application/json",
    "response_schema": GEMINI_SCHEMA,
}

parse_start_time = time.perf_counter()
if TEST:
    response_text = sample_data.response
    tokens_used = 1000
else:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt_parts,
        config=generation_config
    )
    response_text = response.text
    tokens_used = response.usage_metadata.total_token_count
    print(f'total token usage: {response.usage_metadata.total_token_count} - cost = ${0.4 / 1000000 * response.usage_metadata.total_token_count}. INVOICES PROCESSABLE PER usd = {1 / (0.4 / 1000000 * response.usage_metadata.total_token_count)}')
runtime_ms = (time.perf_counter() - parse_start_time) * 1000

# 5. Process the response
try:
    extracted_data = json.loads(response_text)
    print("Successfully extracted data:")
    print(json.dumps(extracted_data, indent=2))

    parsed_invoice = ParsedInvoice(**extracted_data)
    metadata = {
        "organisation_id": 1,
        "image_id": 1,
        "parse_duration_ms": runtime_ms,
        "parse_ai_tokens": tokens_used
    }

    invoice_to_save = Invoice(
        **parsed_invoice.invoice_details.model_dump(),
        **metadata
    )
    line_items_to_save = [
        LineItem(**item.model_dump()) for item in parsed_invoice.line_items
    ]
    invoice_to_save.line_items = line_items_to_save

    print("success?")
    # how to change to a
    # todo - make this a sqlmodel and try pushing to db (need to make tables first)  Will need 2 tables

except (json.JSONDecodeError, AttributeError, IndexError) as e:
    print(f"Could not extract or parse JSON data. Error: {e}")
    try:
        print("Model response text:", response.text)
    except Exception:
        print("Could not get model.text, printing full response object:")
        print(response)
