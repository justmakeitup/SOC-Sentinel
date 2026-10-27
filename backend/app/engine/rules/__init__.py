"""Export all built-in detection rules."""

from app.engine.rules.login_after_failures import LoginAfterFailuresRule
from app.engine.rules.port_scan import PortScanRule
from app.engine.rules.repeated_failed_logins import RepeatedFailedLoginsRule
from app.engine.rules.unusual_auth import UnusualAuthRule

__all__ = [
    "RepeatedFailedLoginsRule",
    "LoginAfterFailuresRule",
    "PortScanRule",
    "UnusualAuthRule",
]
