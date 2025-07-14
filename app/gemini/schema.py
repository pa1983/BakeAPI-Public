import json

from app.models.invoice import ParsedInvoice, ParsedInvoiceDetails, ParsedLineItem

# Get standard schema (which will include $defs and $refs)
schema = ParsedInvoice.model_json_schema()

# Inline $refs
def inline_refs(schema: dict) -> dict:
    # gemini doesn't play nicely with inline refs - need to be removed and replaced with explicit/duplicate refs
    defs = schema.pop("$defs", {})

    def resolve_ref(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_key = obj["$ref"].split("/")[-1]
                resolved = defs.get(ref_key)
                if not resolved:
                    return {"type": "null"}
                return resolve_ref(resolved)
            else:
                return {k: resolve_ref(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_ref(item) for item in obj]
        else:
            return obj

    return resolve_ref(schema)


def clean_and_gemini_normalize(obj):
    # gemini allows only one datatype per field - need to replace anyOf with a specific type.
    # Where database schemas or pydantaic models allow a datatype | null, gemini assumes the null, so remove it and leave
    # only the explicit datatype
    if isinstance(obj, dict):
        obj.pop("title", None)
        obj.pop("default", None)

        # Convert anyOf: [{type: X}, {type: "null"}] → type: X (remove null)
        if "anyOf" in obj:
            # Find the first non-null type
            for item in obj["anyOf"]:
                if isinstance(item, dict) and "type" in item and item["type"] != "null":
                    obj["type"] = item["type"]
                    break
            obj.pop("anyOf", None)

        # If type is a list (e.g. ["string", "null"]), reduce to first non-null type
        if isinstance(obj.get("type"), list):
            non_null_types = [t for t in obj["type"] if t != "null"]
            obj["type"] = non_null_types[0] if non_null_types else "string"  # fallback to string

        for key, value in obj.items():
            clean_and_gemini_normalize(value)
    elif isinstance(obj, list):
        for item in obj:
            clean_and_gemini_normalize(item)

schema = inline_refs(schema)
clean_and_gemini_normalize(schema)
GEMINI_SCHEMA = schema