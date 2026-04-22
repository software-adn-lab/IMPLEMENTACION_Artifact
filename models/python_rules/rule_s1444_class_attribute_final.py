import ast
from typing import List

from .rule_issue import RuleIssue


class S1444ClassAttributeFinalRule:
    # [NUEVO] Detecta atributos de clase no constantes/no Final.
    def check_member(self, member: ast.stmt, file_path: str) -> List[RuleIssue]:
        if isinstance(member, ast.Assign):
            issues: List[RuleIssue] = []
            for target in member.targets:
                if isinstance(target, ast.Name):
                    issue = self._build_issue(target.id, target.lineno, file_path)
                    if issue is not None:
                        issues.append(issue)
            return issues

        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
            target_name = member.target.id
            if self._annotation_contains_final(member.annotation):
                return []
            issue = self._build_issue(target_name, member.lineno, file_path)
            return [issue] if issue is not None else []

        return []

    def _build_issue(self, name: str, line: int, file_path: str):
        if name.startswith("__") and name.endswith("__"):
            return None
        if name.isupper():
            return None

        return RuleIssue(
            rule_key="S1444",
            file_path=file_path,
            line=line,
            message=f"Make this class attribute '{name}' a constant (UPPER_CASE) or Final.",
            symbol_name=name,
            metric_name="USE_GLOBAL_VARIABLE",
            textRange={
                "startLine": line,
                "endLine": line,
            },
        )

    def _annotation_contains_final(self, annotation: ast.AST) -> bool:
        if isinstance(annotation, ast.Name):
            return annotation.id == "Final"
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == "Final"
        if isinstance(annotation, ast.Subscript):
            return self._annotation_contains_final(annotation.value)
        if isinstance(annotation, ast.Constant):
            return str(annotation.value).endswith("Final")
        return False
