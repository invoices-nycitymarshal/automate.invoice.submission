import re

def safe_filename_part(value: object) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", str(value))

    # full transparency: chatgbt generated the return statement
    # i would have sat here all day making sure it was correct

def normalize_billing_code():
    return 0