"""Parser registry for Sentinel log ingestion."""

from app.ingestion.parsers.auth_parser import AuthLogParser
from app.ingestion.parsers.base import BaseLogParser, ParseResult, RawRecord, RejectedRecord
from app.ingestion.parsers.firewall_parser import FirewallLogParser
from app.ingestion.parsers.generic_parser import GenericLogParser

__all__ = [
    "BaseLogParser",
    "RawRecord",
    "RejectedRecord",
    "ParseResult",
    "AuthLogParser",
    "FirewallLogParser",
    "GenericLogParser",
]
