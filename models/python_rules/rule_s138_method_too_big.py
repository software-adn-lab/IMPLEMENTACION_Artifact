import ast
from typing import List, Optional, Tuple

from .rule_issue import RuleIssue


class S138MethodTooBigRule:
    # [NUEVO] Detecta metodos/funciones con LOC por encima del umbral.
    def __init__(self, max_method_lines: int):
        self.max_method_lines = max_method_lines

    def check_callable(self, node: ast.AST, file_path: str, source_lines: List[str]) -> List[RuleIssue]:
        if not hasattr(node, "body") or not getattr(node, "body"):
            return []

        block_start, block_end = self._get_block_line_range(node)
        if block_start is None or block_end is None:
            return []

        lines_of_code = self._count_non_empty_non_comment_lines(source_lines, block_start, block_end)
        if lines_of_code <= self.max_method_lines:
            return []

        name = getattr(node, "name", "<unknown>")
        line = getattr(node, "lineno", 1)
        return [
            RuleIssue(
                rule_key="S138",
                file_path=file_path,
                line=line,
                message=(
                    f"This method/function has {lines_of_code} lines, which is greater than "
                    f"the {self.max_method_lines} lines authorized. "
                    "Split it into smaller methods/functions."
                ),
                symbol_name=name,
                metric_name="LOC_METHOD VERY_HIGH",
                textRange={
                    "startLine": block_start,
                    "endLine": block_end,
                },
            )
        ]

    def _get_block_line_range(self, node: ast.AST) -> Tuple[Optional[int], Optional[int]]:
        body = getattr(node, "body", None)
        if not body:
            return None, None

        first_stmt = body[0]
        start = getattr(first_stmt, "lineno", None)

        end = None
        for stmt in body:
            stmt_end = getattr(stmt, "end_lineno", getattr(stmt, "lineno", None))
            if stmt_end is not None:
                end = max(end or stmt_end, stmt_end)

        return start, end

    def _count_non_empty_non_comment_lines(
        self,
        source_lines: List[str],
        start_line: int,
        end_line: int,
    ) -> int:
        start_index = max(start_line - 1, 0)
        end_index = min(end_line, len(source_lines))

        loc = 0
        for line in source_lines[start_index:end_index]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                loc += 1
        return loc
