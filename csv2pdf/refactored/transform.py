from __future__ import annotations
from models import InvoiceRange, PageRecord

def fill_missing_billing_codes(records: list[PageRecord]) -> list[PageRecord]:
    invoice_to_billing: dict[str, str] = {}
    for record in records:
        if record.billing_code:
            invoice_to_billing[record.invoice_number] = record.billing_code

    return [
        PageRecord(
            absolute_page=record.absolute_page,
            invoice_number=record.invoice_number,
            invoice_page=record.invoice_page,
            billing_code=record.billing_code or invoice_to_billing.get(record.invoice_number),
            source=record.source,
        )
        for record in records
    ]

def group_invoice_ranges(records: list[PageRecord]) -> list[InvoiceRange]:
    if not records:
        return []

    normalized_records = fill_missing_billing_codes(records)
    ranges: list[InvoiceRange] = []

    current = normalized_records[0]
    start_page = current.absolute_page
    prev_page = current.absolute_page

    for record in normalized_records[1:]:
        if record.invoice_number != current.invoice_number:
            ranges.append(
                InvoiceRange(
                    invoice_number=current.invoice_number,
                    billing_code=current.billing_code or "UNKNOWN",
                    absolute_start_page=start_page,
                    absolute_end_page=prev_page,
                )
            )
            current = record
            start_page = record.absolute_page
        prev_page = record.absolute_page

    ranges.append(
        InvoiceRange(
            invoice_number=current.invoice_number,
            billing_code=current.billing_code or "UNKNOWN",
            absolute_start_page=start_page,
            absolute_end_page=prev_page,
        )
    )
    return ranges