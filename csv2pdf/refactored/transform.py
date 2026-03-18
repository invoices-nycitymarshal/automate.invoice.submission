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