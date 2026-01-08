from __future__ import annotations

from email.message import EmailMessage 
from pathlib import Path


def build_subject(invoice_number: int) -> str:
    return f"Client Invoice(s) No.: {invoice_number}"

def build_body() -> str:
    return """Hello,

Attached, please see the following invoice.

Thanks.

– Marshal Grossman and Bailey
"""