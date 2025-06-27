import json
import pathlib
from google import genai
from google.genai.types import Tool, FunctionDeclaration, Part

from schema import GEMINI_SCHEMA
from app.core.config import settings
from app.models.invoice import ParsedInvoice

client = genai.Client(api_key=settings.GEMINI_API_KEY)

PROMPT_INSTRUCTIONS = """
parse this invoice, using the descriptions of fields in the schema for guidance. 
If you can't find exact matches look for something similar. 
Attempt to convert any vat codes to actual vat percentages and present as a floating point number
- code tables should be available in the document.
"""

MODEL =  "gemini-2.5-flash-lite-preview-06-17"  # how will this change over time to match the current preview version?  need to call ListModels and find current relevant model

path_to_pdf = r"C:\Users\44784\Downloads\sysco SalesInvoice-Report.pdf"

# Define the tool during instantiation
invoice_parser_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="extract_invoice_data",
            description="Extracts data from invoice as per the provided schema",
            parameters=GEMINI_SCHEMA  # only changes if change the fields to be pulled from invoices
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

response = client.models.generate_content(
    model=MODEL,
    contents=prompt_parts,
    config=generation_config
)

# 5. Process the response
try:
    print(f'total token usage: {response.usage_metadata.total_token_count} - cost = ${0.4/1000000*response.usage_metadata.total_token_count}. INVOICES PROCESSABLE PER usd = {1/ (0.4/1000000*response.usage_metadata.total_token_count)}')
    extracted_data = json.loads(response.text)
    print("Successfully extracted data:")
    print(json.dumps(extracted_data, indent=2))
    parsed_invoice = ParsedInvoice(**extracted_data)
    # todo - make this a sqlmodel and try pushing to db (need to make tables first)  Will need 2 tables

except (json.JSONDecodeError, AttributeError, IndexError) as e:
    print(f"Could not extract or parse JSON data. Error: {e}")
    try:
        print("Model response text:", response.text)
    except Exception:
        print("Could not get model.text, printing full response object:")
        print(response)