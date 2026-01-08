from __future__ import annotations
from email.message import EmailMessage 
from pathlib import Path
from typing import Optional
from affix.recipients import add_recipients

def write_subject(invoice_number: int) -> str:
    return f"Client Invoice(s) No.: {invoice_number}"

def write_body() -> str:
    return """Hello,

Attached, please see the following invoice.

Thanks.

– Marshal Grossman and Bailey
"""

def build_email_msg(
        client_id: str,
        invoice_num: int,
        pdf_path: Path,
        sender_email: str,

) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["Subject"] = write_subject(invoice_num)
    msg.set_content(write_body())

    pdf_bytes = pdf_path.read_bytes()
    msg.add_attachment(
        pdf_bytes,
        maintype = "application",
        subtype = "pdf",
        filename = pdf_path.name,
    )

def save_eml_draft(
        

) -> Path:
        print()