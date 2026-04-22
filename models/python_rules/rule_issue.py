from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RuleIssue:
    rule_key: str
    file_path: str
    line: int
    message: str
    symbol_name: Optional[str] = None
    source: str = "local"
    severity: str = "MAJOR"
    metric_name: Optional[str] = None
    textRange: Optional[Dict] = None
