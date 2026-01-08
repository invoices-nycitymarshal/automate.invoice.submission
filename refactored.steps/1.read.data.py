import os
import re

from typing import List, Tuple


def parse_filename(filename: str) -> Tuple[str, int]:

    base_name = os.path.basename(filename)

    pattern = r'^([A-Z]{3}) (\d{5})\.pdf$'

    match = re.match(pattern, base_name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(
            f"Invalid filename format: '{base_name}'. "
            "Expected format: 'ABC 12345.pdf'"
        )
    
    client_id = match.group(1).upper()
    invoice_id = int(match.group(2))

    return client_id, invoice_id