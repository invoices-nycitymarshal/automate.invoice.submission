def create_gmail_draft(
    email_msg,
    attachment_path: str
) -> str:
    """
    Attaches PDF and uploads draft to Gmail
    Returns draft_id
    """