"""Registry for Sentinel detection rules."""

import logging
from typing import Dict, List, Optional

from app.engine.base import BaseDetectionRule

logger = logging.getLogger(__name__)


class RuleRegistry:
    """Central registry tracking active and available detection rules."""

    def __init__(self) -> None:
        self._rules: Dict[str, BaseDetectionRule] = {}

    def register(self, rule: BaseDetectionRule) -> None:
        """Registers a rule plugin instance."""
        if rule.rule_code in self._rules:
            logger.warning("Overwriting existing rule registration: %s", rule.rule_code)
        self._rules[rule.rule_code] = rule
        logger.debug("Registered detection rule %s (%s)", rule.rule_code, rule.name)

    def get(self, rule_code: str) -> Optional[BaseDetectionRule]:
        """Retrieves rule by code."""
        return self._rules.get(rule_code)

    def get_all(self) -> List[BaseDetectionRule]:
        """Returns all registered rules."""
        return list(self._rules.values())

    def codes(self) -> List[str]:
        """Returns all registered rule codes."""
        return list(self._rules.keys())


default_registry = RuleRegistry()
