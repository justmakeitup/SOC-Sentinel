"""Parser for synthetic authentication event telemetry (CSV and JSON)."""

import csv
import io
import json

from app.ingestion.parsers.base import BaseLogParser, ParseResult, RawRecord, RejectedRecord


class AuthLogParser(BaseLogParser):
    """Parses authentication logs formatted as CSV, JSON array, or Newline Delimited JSON."""

    def parse_content(self, content_str: str) -> ParseResult:
        result = ParseResult()
        content = content_str.strip()
        if not content:
            return result

        # Check if JSON array or JSON object
        if content.startswith("[") or content.startswith("{"):
            self._parse_json(content, result)
        else:
            self._parse_csv(content, result)

        return result

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
                            reason="Expected JSON object within array",
                            raw_snippet=str(entry),
                        )
                    )
                    continue

                result.valid_records.append(
                    RawRecord(
                        line_number=idx,
                        data=entry,
                        raw_text=json.dumps(entry),
                    )
                )
        except json.JSONDecodeError as err:
            # Fallback: test line-by-line NDJSON
            lines = content.splitlines()
            for idx, line in enumerate(lines, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    entry = json.loads(clean_line)
                    if isinstance(entry, dict):
                        result.valid_records.append(
                            RawRecord(
                                line_number=idx,
                                data=entry,
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
                            reason=f"Invalid JSON syntax: {err.msg}",
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
                header = [h.strip().lower() for h in row]
                continue

            if len(row) != len(header):
                result.rejected_records.append(
                    RejectedRecord(
                        line_number=idx,
                        reason=f"Column count mismatch: expected {len(header)} columns, found {len(row)}",
                        raw_snippet=",".join(row),
                    )
                )
                continue

            row_dict = {header[i]: row[i].strip() for i in range(len(header))}
            from app.ingestion.sanitizer import sanitize_csv_row
            sanitized_raw = sanitize_csv_row(header, row)
            result.valid_records.append(
                RawRecord(
                    line_number=idx,
                    data=row_dict,
                    raw_text=sanitized_raw,
                )
            )
