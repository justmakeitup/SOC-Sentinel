"""Secure CSV export utility with mitigation against Spreadsheet Formula Injection (CWE-1236)."""

import csv
import io
from typing import Any, List


def sanitize_csv_cell(value: Any) -> str:
    """Neutralizes formula injection threats in spreadsheet software (Excel, LibreOffice).

    If a text cell begins with dangerous formula execution operators:
    '=', '+', '-', '@', '\\t', or '\\r', it is prefixed with a single quote (')
    forcing spreadsheet parsers to interpret the cell strictly as a text literal.
    """
    if value is None:
        return ""

    val_str = str(value)
    if not val_str:
        return ""

    # Formula injection trigger characters
    dangerous_prefixes = ("=", "+", "-", "@", "\t", "\r")
    if val_str[0] in dangerous_prefixes:
        # Prepend single quote
        return f"'{val_str}"

    return val_str


def build_csv_response(headers: List[str], rows: List[List[Any]]) -> str:
    """Converts structured rows into sanitized, RFC 4180-compliant CSV content."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Write sanitized header row
    sanitized_headers = [sanitize_csv_cell(h) for h in headers]
    writer.writerow(sanitized_headers)

    # Write sanitized data rows
    for row in rows:
        sanitized_row = [sanitize_csv_cell(cell) for cell in row]
        writer.writerow(sanitized_row)

    return output.getvalue()
