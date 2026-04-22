import ast
from typing import List

from .rule_issue import RuleIssue


class NewNmnoparamVeryHighRule:
    # [NUEVO] NMNOPARAM VERY_HIGH: muchos metodos sin parametros.
    # Ajusta no_param_methods_threshold para controlar sensibilidad.
    def __init__(self, no_param_methods_threshold: int = 6, ignore_dunder: bool = True):
        self.no_param_methods_threshold = no_param_methods_threshold
        self.ignore_dunder = ignore_dunder

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        no_param_count = 0
        for member in node.body:
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if self.ignore_dunder and member.name.startswith("__") and member.name.endswith("__"):
                continue
            if self._has_no_explicit_parameters(member):
                no_param_count += 1

        if no_param_count < self.no_param_methods_threshold:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NMNOPARAM-VERY-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has {no_param_count} methods without parameters, "
                    f"which is above the threshold {self.no_param_methods_threshold}."
                ),
                symbol_name=node.name,
                metric_name="NMNOPARAM VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _has_no_explicit_parameters(self, node: ast.AST) -> bool:
        args = getattr(node, "args", None)
        if args is None:
            return False

        positional = list(getattr(args, "posonlyargs", [])) + list(getattr(args, "args", []))
        if positional and positional[0].arg in {"self", "cls"}:
            positional = positional[1:]

        has_extra_positional = len(positional) > 0
        has_vararg = getattr(args, "vararg", None) is not None
        has_kwonly = len(getattr(args, "kwonlyargs", [])) > 0
        has_kwarg = getattr(args, "kwarg", None) is not None

        return not (has_extra_positional or has_vararg or has_kwonly or has_kwarg)
