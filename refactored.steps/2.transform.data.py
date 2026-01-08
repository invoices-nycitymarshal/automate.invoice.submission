from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
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
    """
    Builds a Gmail-compatible EmailMessage, attaches the PDF,
    and populates the 'To' field via affix.recipients.
    """
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["Subject"] = write_subject(invoice_num)
    msg.set_content(write_body())

    # Attach PDF
    pdf_bytes = pdf_path.read_bytes()
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_path.name,
    )

    # Add recipients to "To:"
    msg = add_recipients(msg=msg, client_id=client_id)

    return msg


def save_eml_draft(
    msg: EmailMessage,
    drafts_dir: Path,
    filename_stem: str,
) -> Path:
    """
    Persist the email draft as an RFC822 .eml file (Gmail-compatible).
    """
    drafts_dir.mkdir(parents=True, exist_ok=True)
    eml_path = drafts_dir / f"{filename_stem}.eml"
    eml_path.write_bytes(msg.as_bytes())
    return eml_path