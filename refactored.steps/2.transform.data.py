def build_subject(invoice_number: int) -> str:
    return f"Client Invoice No.: {invoice_number}"

def build_body() -> str:
    return """Hello,

Attached, please see the following client invoice.

Thanks.

– Marshal Grossman and Bailey
"""
