import re
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pdfplumber
import pytesseract
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image

from apps.dashboard.services import log_activity
from apps.extraction.models import ExtractionResult
from apps.subscriptions.services import enforce_daily_number_limit
from apps.uploads.models import UploadedFile

PHONE_PATTERN = re.compile(r"(\+?\d[\d\s-]{8,15}\d)")


def read_pdf(uploaded_file):
    text_parts = []
    with pdfplumber.open(uploaded_file.file.path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def read_excel(uploaded_file):
    text_parts = []
    workbook = pd.ExcelFile(uploaded_file.file.path)
    for sheet_name in workbook.sheet_names:
        frame = workbook.parse(sheet_name=sheet_name, dtype=str).fillna("")
        text_parts.append(frame.to_string(index=False))
    return "\n".join(text_parts)


def read_csv(uploaded_file):
    frame = pd.read_csv(uploaded_file.file.path, dtype=str).fillna("")
    return frame.to_string(index=False)


def read_image(uploaded_file):
    with Image.open(uploaded_file.file.path) as image:
        return pytesseract.image_to_string(image)


def read_uploaded_content(uploaded_file):
    readers = {
        UploadedFile.FileTypeChoices.PDF: read_pdf,
        UploadedFile.FileTypeChoices.EXCEL: read_excel,
        UploadedFile.FileTypeChoices.CSV: read_csv,
        UploadedFile.FileTypeChoices.IMAGE: read_image,
    }
    return readers[uploaded_file.file_type](uploaded_file)


def normalize_phone_number(raw_number):
    digits = re.sub(r"\D", "", raw_number)
    if not digits:
        return None

    if digits.startswith("00"):
        digits = digits[2:]

    if digits.startswith("971") and len(digits) == 12:
        return f"+971{digits[3:]}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+91{digits[2:]}"
    if len(digits) == 10 and digits.startswith("05"):
        return f"+971{digits[1:]}"
    if len(digits) == 9 and digits.startswith("5"):
        return f"+971{digits}"
    if len(digits) == 11 and digits.startswith("0") and digits[1] == "5":
        return f"+971{digits[1:]}"
    if len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    if len(digits) == 10:
        return f"+91{digits}"
    return None


def extract_numbers(raw_text):
    matches = PHONE_PATTERN.findall(raw_text or "")
    normalized = [normalize_phone_number(match) for match in matches]
    cleaned = [number for number in normalized if number]
    return list(dict.fromkeys(cleaned))


def export_numbers_to_excel(result):
    dataframe = pd.DataFrame({"phone_number": result.numbers})
    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    buffer.seek(0)

    result_filename = f"{Path(result.upload.original_name).stem[:50]}_{uuid4().hex}.xlsx"
    if result.result_file:
        result.result_file.delete(save=False)
    result.result_file.save(result_filename, ContentFile(buffer.getvalue()), save=False)
    result.save(update_fields=["result_file", "updated_at"])
    return result


def process_uploaded_file(uploaded_file):
    uploaded_file.status = UploadedFile.StatusChoices.PROCESSING
    uploaded_file.error_message = ""
    uploaded_file.save(update_fields=["status", "error_message"])

    try:
        content = read_uploaded_content(uploaded_file)
        numbers = extract_numbers(content)
        try:
            existing_total = uploaded_file.extraction_result.total_numbers
        except UploadedFile.extraction_result.RelatedObjectDoesNotExist:
            existing_total = 0
        enforce_daily_number_limit(uploaded_file.user, len(numbers), existing_total=existing_total)

        result, _ = ExtractionResult.objects.update_or_create(
            upload=uploaded_file,
            defaults={
                "user": uploaded_file.user,
                "numbers": numbers,
                "total_numbers": len(numbers),
            },
        )
        export_numbers_to_excel(result)

        uploaded_file.status = UploadedFile.StatusChoices.COMPLETED
        uploaded_file.processed_at = timezone.now()
        uploaded_file.error_message = ""
        uploaded_file.save(update_fields=["status", "processed_at", "error_message"])

        log_activity(
            user=uploaded_file.user,
            action="extraction_completed",
            description=f"Processed {uploaded_file.original_name}.",
            metadata={
                "upload_id": str(uploaded_file.id),
                "result_id": str(result.id),
                "total_numbers": result.total_numbers,
            },
        )
        return result
    except Exception as exc:
        uploaded_file.status = UploadedFile.StatusChoices.FAILED
        uploaded_file.error_message = str(exc)
        uploaded_file.processed_at = timezone.now()
        uploaded_file.save(update_fields=["status", "error_message", "processed_at"])

        log_activity(
            user=uploaded_file.user,
            action="extraction_failed",
            description=f"Failed to process {uploaded_file.original_name}.",
            metadata={"upload_id": str(uploaded_file.id), "error": str(exc)},
        )
        raise
