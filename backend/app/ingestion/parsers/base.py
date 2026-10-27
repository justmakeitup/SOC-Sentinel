"""Base classes and data structures for telemetry parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.ingestion.sanitizer import sanitize_raw_payload


@dataclass
class RawRecord:
    """An unnormalized extracted record paired with its origin line index."""
    line_number: int
    data: Dict[str, Any]
    raw_text: str


@dataclass
class RejectedRecord:
    """A record that failed format or syntax parsing."""
    line_number: int
    reason: str
    raw_snippet: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "reason": self.reason,
            "raw_snippet": sanitize_raw_payload(self.raw_snippet)[:200],
        }


@dataclass
class ParseResult:
    """Aggregate result from a parser execution."""
    valid_records: List[RawRecord] = field(default_factory=list)
    rejected_records: List[RejectedRecord] = field(default_factory=list)


class BaseLogParser(ABC):
    """Abstract interface implemented by all format-specific telemetry parsers."""

    @abstractmethod
    def parse_content(self, content_str: str) -> ParseResult:
        """Parses the raw file content into records, handling syntax errors safely."""
        pass
