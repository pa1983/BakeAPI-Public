import json
from unittest.mock import MagicMock
import pytest
from app.gemini import gemini
from app.models.invoice import ParsedInvoice

MOCK_GEMINI_RESPONSE = """{
  "line_items": [
    {
      "cases": 0,
      "units": 0,
      "description": "2 L CLANDEBOYE GREEK YOG",
      "size": "2 L",
      "code": "NG2",
      "value_ex_vat": 22.85,
      "value_inc_vat": 22.85,
      "vat_percentage": 0.00,
      "is_delivery": false
    },
    {
      "cases": 0,
      "units": 0,
      "description": "2 LIT JUG SEMI SKIM",
      "size": "2 LIT",
      "code": "SS4",
      "value_ex_vat": 7.30,
      "value_inc_vat": 7.30,
      "vat_percentage": 0.00,
      "is_delivery": false
    },
    {
      "cases": 0,
      "units": 0,
      "description": "2 LIT JUG WHOLE MILK",
      "size": "2 LIT",
      "code": "WM4",
      "value_ex_vat": 78.84,
      "value_inc_vat": 78.84,
      "vat_percentage": 0.00,
      "is_delivery": false
    }
  ],
  "invoice_details": {
    "supplier_name": "Draynes Farm",
    "customer_account_number": "E628",
    "invoice_number": "26309",
    "user_reference": "E628",
    "supplier_reference": "E628",
    "calculated_total": 108.99,
    "invoice_total": 108.99,
    "delivery_cost": 0.00,
    "parsed_currency": "GBP",
    "document_type": "INVOICE",
    "invoice_date": "2024-08-17",
    "confidence_score": 0.9
  }
}"""
def test_extract_gemini_response_success():
    """
    Tests successful extraction with a valid Gemini response.
    """
    # Arrange: Create a mock response object that mimics the real one
    mock_response = MagicMock()
    # Assign the raw dummy string
    mock_response.text = MOCK_GEMINI_RESPONSE

    # Act
    result = gemini.extract_gemini_response(mock_response)

    # Assert
    assert isinstance(result, ParsedInvoice)

    # FIX 2: Update assertions to match the actual mock data
    assert result.invoice_details.supplier_name == "Draynes Farm"
    assert len(result.line_items) == 3
    assert result.invoice_details.invoice_number == "26309"
    assert result.invoice_details.invoice_total == 108.99

def test_extract_gemini_response_invalid_json():
    """
    Tests that the function raises an error with malformed JSON.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.text = "this is not valid json"

    # Act & Assert
    with pytest.raises(json.JSONDecodeError):
        gemini.extract_gemini_response(mock_response)