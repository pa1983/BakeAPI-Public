# for use when testing functionality without need to make API calls to gemini

response = """{
  "line_items": [
    {
      "cases": 1,
      "units": 0,
      "description": "BRAKES ESSENTIALS BLEACH",
      "size": "2x5 LT",
      "code": "136383",
      "value_ex_vat": 8.14,
      "value_inc_vat": 8.14,
      "vat_percentage": 0.0
    },
    {
      "cases": 0,
      "units": 6,
      "description": "SYSCO ESSENTIAL GROUND ALMONDS",
      "size": "1x1 KG",
      "code": "494672",
      "value_ex_vat": 47.40,
      "value_inc_vat": 47.40,
      "vat_percentage": 0.2
    },
    {
      "cases": 1,
      "units": 0,
      "description": "BLUE CENTREFEED ROLL 2PLY",
      "size": "1x6'S",
      "code": "PD9815",
      "value_ex_vat": 8.14,
      "value_inc_vat": 8.14,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 1,
      "description": "RED PLUMS PUNNET",
      "size": "1x1 KG",
      "code": "FW586",
      "value_ex_vat": 4.69,
      "value_inc_vat": 4.69,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 3,
      "description": "RASPBERRIES",
      "size": "1x1'S",
      "code": "FW600",
      "value_ex_vat": 7.68,
      "value_inc_vat": 7.68,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 2,
      "description": "LEMONS NET",
      "size": "1x6'S",
      "code": "FW611",
      "value_ex_vat": 3.40,
      "value_inc_vat": 3.40,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 1,
      "description": "MEDIUM ONIONS (NET OF 3)",
      "size": "1x1 KG",
      "code": "VW810",
      "value_ex_vat": 2.04,
      "value_inc_vat": 2.04,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 1,
      "description": "MINT (FRESH HERB)",
      "size": "1x100 GM",
      "code": "491008",
      "value_ex_vat": 1.92,
      "value_inc_vat": 1.92,
      "vat_percentage": 0.2
    },
    {
      "cases": 0,
      "units": 2,
      "description": "LIMES",
      "size": "1x6'S",
      "code": "FW580",
      "value_ex_vat": 3.06,
      "value_inc_vat": 3.06,
      "vat_percentage": 0.2
    },
    {
      "cases": 1,
      "units": 0,
      "description": "VINE TOMATOES",
      "size": "1x5 KG",
      "code": "TM194",
      "value_ex_vat": 16.14,
      "value_inc_vat": 16.14,
      "vat_percentage": 0.2
    }
  ],
  "invoice_details": {
    "supplier_name": "Sysco",
    "invoice_number": "39723390",
    "calculated_total": 102.61,
    "invoice_total": 105.87,
    "delivery_cost": 0.0,
    "currency": "GBP",
    "invoice_date": "2506-06-20 20:00:00+00:00",
    "confidence_score": 0.9
  }
}"""