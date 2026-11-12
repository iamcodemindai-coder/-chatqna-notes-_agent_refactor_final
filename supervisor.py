# import logging
# from typing import Any

# logger = logging.getLogger(__name__)

# CHAT_FIELD = "Chatqna"
# UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "na"}

# CONTACT_FIELDS = [
#     "contact_type", "contact_role", "first_name", "last_name",
#     "phone_number", "additional_phone_number", "email_address",
#     "date_of_birth", "gender", "address", "street", "city",
#     "zip_postal_code", "state_province", "country",
# ]

# CONSENT_FIELD_MAPPING = {
#     "permission_to_contact_hcp": "Permission To Contact HCP",
#     "permission_to_contact_reporter": "Permission To Contact Reporter",
#     "permission_to_contact_patient": "Permission To Contact Patient",
#     "permission_to_contact_complaint": "Permission To Contact Complaint",
#     "permission_to_contact_reporter_via_text": "Permission To Contact Via Text",
# }


# def unknown(value):
#     if value is None:
#         return "Unknown"
#     if isinstance(value, str) and value.strip().lower() in UNKNOWN_VALUES:
#         return "Unknown"
#     return value


# def get_chatqna(input_data):
#     if not isinstance(input_data, dict):
#         return ""
#     value = input_data.get("Chatqna", input_data.get("chatqna", ""))
#     return value if isinstance(value, str) else str(value or "")


# def get_notes(input_data):
#     if not isinstance(input_data, dict):
#         return ""
#     value = input_data.get("Notes", input_data.get("notes", ""))
#     return value if isinstance(value, str) else str(value or "")


# def _clean_value(value):
#     value = unknown(value)
#     return None if value == "Unknown" else value


# def _comparison_key(value, field=None):
#     if not isinstance(value, str):
#         return value
#     normalized = " ".join(value.strip().casefold().split())
#     if field == "contact_role":
#         return tuple(sorted(part.strip() for part in normalized.split(",") if part.strip()))
#     return normalized


# def _contact_records(source_result):
#     if not isinstance(source_result, dict):
#         return []
#     records = source_result.get("chat_response", [])
#     return records if isinstance(records, list) else []


# def _field_parts(contact_record, field):
#     raw = contact_record.get(field) if isinstance(contact_record, dict) else None
#     if isinstance(raw, dict):
#         value = _clean_value(raw.get("value"))
#         evidence = raw.get("evidence", [])
#     else:
#         value = _clean_value(raw)
#         evidence = []
#     return value, evidence if evidence is not None else []


# def create_chat_response(contact_result):
#     """Compare Chatqna and Notes contact fields without another LLM call."""
#     if not isinstance(contact_result, dict):
#         contact_result = {}
#     chat_source = contact_result.get("chatqna", {})
#     notes_source = contact_result.get("notes", {})
#     chat_contacts = _contact_records(chat_source)
#     notes_contacts = _contact_records(notes_source)

#     compared_contacts = []
#     count = max(len(chat_contacts), len(notes_contacts), 1)
#     for index in range(count):
#         chat_contact = chat_contacts[index] if index < len(chat_contacts) and isinstance(chat_contacts[index], dict) else {}
#         notes_contact = notes_contacts[index] if index < len(notes_contacts) and isinstance(notes_contacts[index], dict) else {}
#         compared_contact = {}

#         for field in CONTACT_FIELDS:
#             chat_value, chat_evidence = _field_parts(chat_contact, field)
#             notes_value, notes_evidence = _field_parts(notes_contact, field)
#             status = "confirm"
#             if chat_value is not None and notes_value is not None:
#                 if _comparison_key(chat_value, field) != _comparison_key(notes_value, field):
#                     status = "conflict"

#             compared_contact[field] = {
#                 "status": status,
#                 "candidates": [
#                     {"value": chat_value, "source": "chatqna", "evidence": chat_evidence},
#                     {"value": notes_value, "source": "notes", "evidence": notes_evidence},
#                 ],
#             }
#         compared_contacts.append(compared_contact)
#     return compared_contacts


# def _consent_field_map(source_result):
#     """Convert the source agent's list/dict representation to field-name mapping."""
#     if not isinstance(source_result, dict):
#         return {}
#     raw_fields = source_result.get("Additional Fields", [])
#     if isinstance(raw_fields, dict):
#         return raw_fields
#     mapped = {}
#     if isinstance(raw_fields, list):
#         for item in raw_fields:
#             if isinstance(item, dict):
#                 mapped.update(item)
#     return mapped


# def normalize_consent_value(value):
#     if isinstance(value, dict):
#         value = value.get("value")
#     if isinstance(value, bool):
#         return "Yes" if value else "No"
#     if value is None:
#         return "Unknown"
#     cleaned = str(value).strip()
#     if cleaned.upper() in {"YES", "Y", "TRUE"}:
#         return "Yes"
#     if cleaned.upper() in {"NO", "N", "FALSE"}:
#         return "No"
#     if cleaned.lower() in UNKNOWN_VALUES:
#         return "Unknown"
#     return cleaned


# def _consent_parts(source_fields, original_field):
#     raw = source_fields.get(original_field)
#     if isinstance(raw, dict):
#         value = normalize_consent_value(raw.get("value"))
#         evidence = raw.get("evidence", [])
#     else:
#         value = normalize_consent_value(raw)
#         evidence = []
#     return value, evidence if evidence is not None else []


# def create_additional_fields(consent_result):
#     """Compare Chatqna and Notes consent fields and retain source evidence."""
#     if not isinstance(consent_result, dict):
#         consent_result = {}
#     chat_fields = _consent_field_map(consent_result.get("chatqna", {}))
#     notes_fields = _consent_field_map(consent_result.get("notes", {}))
#     output = {}

#     for output_field, original_field in CONSENT_FIELD_MAPPING.items():
#         chat_value, chat_evidence = _consent_parts(chat_fields, original_field)
#         notes_value, notes_evidence = _consent_parts(notes_fields, original_field)
#         status = "confirm"
#         if chat_value != "Unknown" and notes_value != "Unknown" and chat_value.casefold() != notes_value.casefold():
#             status = "conflict"
#         output[output_field] = {
#             "status": status,
#             "candidates": [
#                 {"value": None if chat_value == "Unknown" else chat_value, "source": "chatqna", "evidence": chat_evidence},
#                 {"value": None if notes_value == "Unknown" else notes_value, "source": "notes", "evidence": notes_evidence},
#             ],
#         }
#     return output


# def format_verbatim(items):
#     if not isinstance(items, list):
#         return []
#     formatted = []
#     for item in items:
#         if isinstance(item, dict) and ("bot" in item or "user" in item):
#             formatted.append({"bot": item.get("bot", "") or "", "user": item.get("user", "") or ""})
#         elif isinstance(item, str) and item.strip():
#             formatted.append(item)
#     return formatted


# def combine_verbatim(contact_result, consent_result):
#     contact_chat = contact_result.get("chatqna", {}) if isinstance(contact_result, dict) else {}
#     consent_chat = consent_result.get("chatqna", {}) if isinstance(consent_result, dict) else {}
#     contact_items = format_verbatim(contact_chat.get("reported_verbatim", [])) if isinstance(contact_chat, dict) else []
#     consent_items = format_verbatim(consent_chat.get("Reported Verbatim", [])) if isinstance(consent_chat, dict) else []
#     combined = []
#     seen = set()
#     for item in contact_items + consent_items:
#         marker = repr(item)
#         if marker not in seen:
#             seen.add(marker)
#             combined.append(item)
#     return combined


# def to_number(value):
#     if value is None:
#         return None
#     try:
#         if isinstance(value, str):
#             value = value.strip().replace("%", "")
#             if not value:
#                 return None
#         return float(value)
#     except (TypeError, ValueError):
#         logger.warning("Unable to convert confidence score to number: %r", value)
#         return None


# def calculate_confidence(contact_result, consent_result):
#     contact_chat = contact_result.get("chatqna", {}) if isinstance(contact_result, dict) else {}
#     consent_chat = consent_result.get("chatqna", {}) if isinstance(consent_result, dict) else {}
#     scores = []
#     if isinstance(contact_chat, dict):
#         score = to_number(contact_chat.get("contact_confidence_score"))
#         if score is not None:
#             scores.append(score)
#     if isinstance(consent_chat, dict):
#         score = to_number(consent_chat.get("Consent Confidence Score"))
#         if score is not None:
#             scores.append(score)
#     return round(sum(scores) / len(scores), 2) if scores else 0


# def create_final_output(input_data, contact_result, consent_result):
#     if not isinstance(input_data, dict):
#         input_data = {}
#     return {
#         "MasterCaseId": input_data.get("MasterCaseId", ""),
#         "AutomationReportId": input_data.get("AutomationReportId", ""),
#         "Confidence": calculate_confidence(contact_result, consent_result),
#         "Reported Verbatim": combine_verbatim(contact_result, consent_result),
#         "ChatResponse": create_chat_response(contact_result),
#         "Additional Fields": create_additional_fields(consent_result),
#     }








import logging
from typing import Any

logger = logging.getLogger(__name__)

CHAT_FIELD = "Chatqna"
UNKNOWN_VALUES = {"", "unknown", "none", "null", "n/a", "na"}

CONTACT_FIELDS = [
    "contact_type", "contact_role", "first_name", "last_name",
    "phone_number", "additional_phone_number", "email_address",
    "date_of_birth", "gender", "address", "street", "city",
    "zip_postal_code", "state_province", "country",
]

CONSENT_FIELD_MAPPING = {
    "permission_to_contact_hcp": "Permission To Contact HCP",
    "permission_to_contact_reporter": "Permission To Contact Reporter",
    "permission_to_contact_patient": "Permission To Contact Patient",
    "permission_to_contact_complaint": "Permission To Contact Complaint",
    "permission_to_contact_reporter_via_text": "Permission To Contact Via Text",
}


def unknown(value):
    if value is None:
        return "Unknown"

    if isinstance(value, str) and value.strip().lower() in UNKNOWN_VALUES:
        return "Unknown"

    return value


def get_chatqna(input_data):
    if not isinstance(input_data, dict):
        return ""

    value = input_data.get("Chatqna", input_data.get("chatqna", ""))
    return value if isinstance(value, str) else str(value or "")


def get_notes(input_data):
    if not isinstance(input_data, dict):
        return ""

    value = input_data.get("Notes", input_data.get("notes", ""))
    return value if isinstance(value, str) else str(value or "")


def _clean_value(value):
    value = unknown(value)
    return None if value == "Unknown" else value


def _comparison_key(value, field=None):
    if not isinstance(value, str):
        return value

    normalized = " ".join(value.strip().casefold().split())

    if field == "contact_role":
        return tuple(
            sorted(
                part.strip()
                for part in normalized.split(",")
                if part.strip()
            )
        )

    return normalized


def _contact_records(source_result):
    if not isinstance(source_result, dict):
        return []

    records = source_result.get("chat_response", [])

    return records if isinstance(records, list) else []


def _field_parts(contact_record, field):
    raw = contact_record.get(field) if isinstance(contact_record, dict) else None

    if isinstance(raw, dict):
        value = _clean_value(raw.get("value"))
        evidence = raw.get("evidence", [])
    else:
        value = _clean_value(raw)
        evidence = []

    return value, evidence if evidence is not None else []


def to_number(value):
    if value is None:
        return None

    try:
        if isinstance(value, str):
            value = value.strip().replace("%", "")

            if not value:
                return None

        return float(value)

    except (TypeError, ValueError):
        logger.warning(
            "Unable to convert confidence score to number: %r",
            value
        )
        return None


# ============================================================
# CONFIDENCE HELPERS
# ============================================================

def _average_available(*scores):
    valid = [
        score for score in scores
        if score is not None
    ]

    return round(sum(valid) / len(valid), 2) if valid else None


def _contact_confidence(chat_contact, notes_contact):
    """
    Calculate confidence for an individual contact.

    Chatqna and Notes scores are retained separately.
    Overall score is their average when both are available.
    """

    chat_score = (
        to_number(chat_contact.get("contact_confidence_score"))
        if chat_contact else None
    )

    notes_score = (
        to_number(notes_contact.get("contact_confidence_score"))
        if notes_contact else None
    )

    return {
        "chatqna": chat_score,
        "notes": notes_score,
        "overall": _average_available(
            chat_score,
            notes_score
        )
    }


# ============================================================
# CONTACT COMPARISON
# ============================================================

def create_chat_response(contact_result):
    """
    Compare Chatqna and Notes contact fields.
    """

    if not isinstance(contact_result, dict):
        contact_result = {}

    chat_source = contact_result.get("chatqna", {})
    notes_source = contact_result.get("notes", {})

    chat_contacts = _contact_records(chat_source)
    notes_contacts = _contact_records(notes_source)

    compared_contacts = []

    count = max(
        len(chat_contacts),
        len(notes_contacts),
        1
    )

    for index in range(count):

        chat_contact = (
            chat_contacts[index]
            if index < len(chat_contacts)
            and isinstance(chat_contacts[index], dict)
            else {}
        )

        notes_contact = (
            notes_contacts[index]
            if index < len(notes_contacts)
            and isinstance(notes_contacts[index], dict)
            else {}
        )

        compared_contact = {}

        for field in CONTACT_FIELDS:

            chat_value, chat_evidence = _field_parts(
                chat_contact,
                field
            )

            notes_value, notes_evidence = _field_parts(
                notes_contact,
                field
            )

            status = "confirm"

            if (
                chat_value is not None
                and notes_value is not None
            ):
                if (
                    _comparison_key(chat_value, field)
                    != _comparison_key(notes_value, field)
                ):
                    status = "conflict"

            compared_contact[field] = {
                "status": status,
                "candidates": [
                    {
                        "value": chat_value,
                        "source": "chatqna",
                        "evidence": chat_evidence
                    },
                    {
                        "value": notes_value,
                        "source": "notes",
                        "evidence": notes_evidence
                    }
                ]
            }

        # NEW: Individual contact confidence
        compared_contact["contact_confidence_score"] = (
            _contact_confidence(
                chat_contact,
                notes_contact
            )
        )

        compared_contacts.append(compared_contact)

    return compared_contacts


# ============================================================
# CONSENT FIELD MAPPING
# ============================================================

def _consent_field_map(source_result):
    """
    Convert source Additional Fields list/dict
    into a field-name mapping.
    """

    if not isinstance(source_result, dict):
        return {}

    raw_fields = source_result.get("Additional Fields", [])

    if isinstance(raw_fields, dict):
        return raw_fields

    mapped = {}

    if isinstance(raw_fields, list):
        for item in raw_fields:
            if isinstance(item, dict):
                mapped.update(item)

    return mapped


def normalize_consent_value(value):

    if isinstance(value, dict):
        value = value.get("value")

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if value is None:
        return "Unknown"

    cleaned = str(value).strip()

    if cleaned.upper() in {"YES", "Y", "TRUE"}:
        return "Yes"

    if cleaned.upper() in {"NO", "N", "FALSE"}:
        return "No"

    if cleaned.lower() in UNKNOWN_VALUES:
        return "Unknown"

    return cleaned


def _consent_parts(source_fields, original_field):

    raw = source_fields.get(original_field)

    if isinstance(raw, dict):
        value = normalize_consent_value(raw.get("value"))
        evidence = raw.get("evidence", [])
    else:
        value = normalize_consent_value(raw)
        evidence = []

    return value, evidence if evidence is not None else []


# ============================================================
# CONSENT CONFIDENCE
# ============================================================

def calculate_consent_confidence(consent_result, input_data=None):
    """
    Calculate separate Consent confidence.

    Ignore an empty source so its default zero score
    does not reduce the available source score.
    """

    if not isinstance(consent_result, dict):
        return None

    input_data = input_data if isinstance(input_data, dict) else {}

    source_inputs = {
        "chatqna": get_chatqna(input_data),
        "notes": get_notes(input_data)
    }

    scores = []

    for source_name in ("chatqna", "notes"):

        # Do not include an empty input source.
        if not source_inputs[source_name].strip():
            continue

        source = consent_result.get(source_name, {})

        if not isinstance(source, dict):
            continue

        score = to_number(
            source.get("Consent Confidence Score")
        )

        if score is not None:
            scores.append(score)

    return _average_available(*scores)


# ============================================================
# ADDITIONAL FIELDS COMPARISON
# ============================================================

def create_additional_fields(consent_result, input_data=None):

    if not isinstance(consent_result, dict):
        consent_result = {}

    chat_fields = _consent_field_map(
        consent_result.get("chatqna", {})
    )

    notes_fields = _consent_field_map(
        consent_result.get("notes", {})
    )

    output = {}

    for output_field, original_field in CONSENT_FIELD_MAPPING.items():

        chat_value, chat_evidence = _consent_parts(
            chat_fields,
            original_field
        )

        notes_value, notes_evidence = _consent_parts(
            notes_fields,
            original_field
        )

        status = "confirm"

        if (
            chat_value != "Unknown"
            and notes_value != "Unknown"
            and chat_value.casefold() != notes_value.casefold()
        ):
            status = "conflict"

        output[output_field] = {
            "status": status,
            "candidates": [
                {
                    "value": None if chat_value == "Unknown" else chat_value,
                    "source": "chatqna",
                    "evidence": chat_evidence
                },
                {
                    "value": None if notes_value == "Unknown" else notes_value,
                    "source": "notes",
                    "evidence": notes_evidence
                }
            ]
        }

    # NEW: Separate Consent Agent confidence
    output["consent_confidence_score"] = (
        calculate_consent_confidence(
            consent_result,
            input_data
        )
    )

    return output


# ============================================================
# REPORTED VERBATIM
# ============================================================

def format_verbatim(items):

    if not isinstance(items, list):
        return []

    formatted = []

    for item in items:

        if isinstance(item, dict) and (
            "bot" in item or "user" in item
        ):
            formatted.append({
                "bot": item.get("bot", "") or "",
                "user": item.get("user", "") or ""
            })

        elif isinstance(item, str) and item.strip():
            formatted.append(item)

    return formatted


def combine_verbatim(contact_result, consent_result):

    contact_chat = (
        contact_result.get("chatqna", {})
        if isinstance(contact_result, dict)
        else {}
    )

    consent_chat = (
        consent_result.get("chatqna", {})
        if isinstance(consent_result, dict)
        else {}
    )

    contact_items = (
        format_verbatim(
            contact_chat.get("reported_verbatim", [])
        )
        if isinstance(contact_chat, dict)
        else []
    )

    consent_items = (
        format_verbatim(
            consent_chat.get("Reported Verbatim", [])
        )
        if isinstance(consent_chat, dict)
        else []
    )

    combined = []
    seen = set()

    for item in contact_items + consent_items:

        marker = repr(item)

        if marker not in seen:
            seen.add(marker)
            combined.append(item)

    return combined


# ============================================================
# EXISTING OVERALL CONFIDENCE
# ============================================================

def calculate_confidence(contact_result, consent_result):
    """
    Existing overall Confidence calculation.
    Kept unchanged.
    """

    contact_chat = (
        contact_result.get("chatqna", {})
        if isinstance(contact_result, dict)
        else {}
    )

    consent_chat = (
        consent_result.get("chatqna", {})
        if isinstance(consent_result, dict)
        else {}
    )

    scores = []

    if isinstance(contact_chat, dict):

        score = to_number(
            contact_chat.get("contact_confidence_score")
        )

        if score is not None:
            scores.append(score)

    if isinstance(consent_chat, dict):

        score = to_number(
            consent_chat.get("Consent Confidence Score")
        )

        if score is not None:
            scores.append(score)

    return round(sum(scores) / len(scores), 2) if scores else 0


# ============================================================
# FINAL OUTPUT
# ============================================================

def create_final_output(input_data, contact_result, consent_result):

    if not isinstance(input_data, dict):
        input_data = {}

    return {
        "MasterCaseId": input_data.get("MasterCaseId", ""),

        "AutomationReportId": input_data.get(
            "AutomationReportId",
            ""
        ),

        # Existing overall confidence remains unchanged.
        "Confidence": calculate_confidence(
            contact_result,
            consent_result
        ),

        "Reported Verbatim": combine_verbatim(
            contact_result,
            consent_result
        ),

        "ChatResponse": create_chat_response(
            contact_result
        ),

        "Additional Fields": create_additional_fields(
            consent_result,
            input_data
        )
    }

