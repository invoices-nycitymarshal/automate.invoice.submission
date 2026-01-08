## ABC 12345.pdf
## │││ ││││││
## │││ └─ 5-digit invoice ID (int)
## └└└── 3-letter client ID (str)  

## goals: regex enforcement, directory safe traversing

import os
import re

def parse_filename(filename: str) -> tuple[str, int]:
    print()

    base_name = os.path.basename(filename)

    pattern = r'^([A-Z]{3}) (\d{5}).pdf$'