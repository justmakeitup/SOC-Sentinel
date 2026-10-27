"""Generic parser for structured JSON arrays, NDJSON, and CSV files with field mappings."""

import csv
import io
import json
from typing import Dict, Optional

from app.ingestion.parsers.base import BaseLogParser, ParseResult, RawRecord, RejectedRecord


class GenericLogParser(BaseLogParser):
    """Parser accommodating structured JSON and custom-mapped CSV files."""

    def __init__(self, field_mapping: Optional[Dict[str, str]] = None):
        self.field_mapping = field_mapping or {}

    def parse_content(self, content_str: str) -> ParseResult:
        result = ParseResult()
        content = content_str.strip()
        if not content:
            return result

        if content.startswith("[") or content.startswith("{"):
            self._parse_json(content, result)
        else:
            self._parse_csv(content, result)

        return result

    def _apply_mapping(self, record_data: Dict[str, str]) -> Dict[str, str]:
        """Maps user-documented column aliases to standard ECS keys."""
        if not self.field_mapping:
            return record_data

        mapped = dict(record_data)
        for target_key, source_key in self.field_mapping.items():
            if source_key in record_data:
                mapped[target_key] = record_data[source_key]
        return mapped

    def _parse_json(self, content: str, result: ParseResult) -> None:
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                parsed = [parsed]

            for idx, entry in enumerate(parsed, start=1):
                if not isinstance(entry, dict):
                    result.rejected_records.append(
                        RejectedRecord(
                            line_number=idx,
                            reason="Record is not a valid JSON key-value map",
                            raw_snippet=str(entry),
                        )
                    )
                    continue

                mapped_data = self._apply_mapping(entry)
                result.valid_records.append(
                    RawRecord(
                        line_number=idx,
                        data=mapped_data,
                        raw_text=json.dumps(entry),
                    )
                )
        except json.JSONDecodeError as err:
            lines = content.splitlines()
            for idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    entry = json.loads(clean_line)
                    if isinstance(entry, dict):
                        mapped_data = self._apply_mapping(entry)
                        result.valid_records.append(
                            RawRecord(
                                line_number=idx,
                                data=mapped_data,
                                raw_text=clean_line,
                            )
                        )
                    else:
                        result.rejected_records.append(
                            RejectedRecord(
                                line_number=idx,
                                reason="JSON line is not an object",
                                raw_snippet=clean_line,
                            )
                        )
                except json.JSONDecodeError:
                    result.rejected_records.append(
                        RejectedRecord(
                            line_number=idx,
                            reason=f"Malformed JSON syntax on line {idx}: {err.msg}",
                            raw_snippet=clean_line,
                        )
                    )

    def _parse_csv(self, content: str, result: ParseResult) -> None:
        reader = csv.reader(io.StringIO(content))
        header: list[str] | None = None

        for idx, row in enumerate(reader, start=1):
            if not row or not any(field.strip() for field in row):
                continue

            if header is None:
                header = [h.strip() for h in row]
                continue

            if len(row) != len(header):
                result.rejected_records.append(
                    RejectedRecord(
                        line_number=idx,
                        reason=f"CSV row column count {len(row)} differs from header count {len(header)}",
                        raw_snippet=",".join(row),
                    )
                )
                continue

            row_dict = {header[i]: row[i].strip() for i in range(len(header))}
            mapped_data = self._apply_mapping(row_dict)
            from app.ingestion.sanitizer import sanitize_csv_row
            sanitized_raw = sanitize_csv_row(header, row)
            result.valid_records.append(
                RawRecord(
                    line_number=idx,
                    data=mapped_data,
                    raw_text=sanitized_raw,
                )
            )
