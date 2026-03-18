from email.message import EmailMessage

def get_recipients(client_code: str) -> list[str]:
    """
    Searches Google Contacts group matching client_code
    Returns list of email addresses
    """

def create_email_instance(
    subject: str,
    body: str,
    sender: str
) -> EmailMessage:
    """
    Creates a new EmailMessage object with subject, body, and sender
    """
    msg = EmailMessage()
    msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(body)
    return msg

def affix_recipients(
    email_msg: EmailMessage,
    recipients: list[str]
) -> EmailMessage:
    """
    Adds recipients to the To: field
    """
    email_msg["To"] = ", ".join(recipients)
    return email_msg
