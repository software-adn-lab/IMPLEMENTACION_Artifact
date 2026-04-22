import ast
from typing import List, Set

from .rule_issue import RuleIssue


class NewNaccVeryHighRule:
    # [NUEVO] NACC VERY_HIGH: interfaz publica muy grande.
    # Ajusta public_access_threshold para subir/bajar sensibilidad.
    def __init__(self, public_access_threshold: int = 12):
        self.public_access_threshold = public_access_threshold

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        public_members = self._collect_public_members(node)
        nacc = len(public_members)
        if nacc < self.public_access_threshold:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NACC-VERY-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' exposes {nacc} public members, "
                    f"which is above the threshold {self.public_access_threshold}."
                ),
                symbol_name=node.name,
                metric_name="NACC VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _collect_public_members(self, node: ast.ClassDef) -> Set[str]:
        members: Set[str] = set()

        for member in node.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not member.name.startswith("_"):
                    members.add(member.name)
                for stmt in ast.walk(member):
                    if isinstance(stmt, ast.Attribute) and isinstance(stmt.value, ast.Name):
                        if stmt.value.id == "self" and not stmt.attr.startswith("_"):
                            members.add(stmt.attr)
            elif isinstance(member, ast.Assign):
                for target in member.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        members.add(target.id)
            elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                if not member.target.id.startswith("_"):
                    members.add(member.target.id)

        return members
