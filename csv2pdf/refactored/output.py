from __future__ import annotations

import csv
import re
from pathlib import Path

import fitz
import pandas as pd

from models import InvoiceRange, PageRecord
from transform import fill_missing_billing_codes