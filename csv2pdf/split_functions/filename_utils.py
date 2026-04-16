import re

def safe_filename_part(value: object) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", str(value))

    # full transparency: chatgbt generated the return statement
    # i would have sat here all day making sure it was correct

def normalize_billing_code(value: object) -> str:
    text = str(value).strip()
    return text if text else "UNKNOWN"