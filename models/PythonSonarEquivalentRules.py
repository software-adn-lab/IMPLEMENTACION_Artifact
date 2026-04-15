import ast
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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


class PythonSonarEquivalentRules:
    """
    Python translation of selected Sonar Java rules.

    Implemented equivalents:
    - S101: BadClassNameCheck
    - S100: BadMethodNameCheck
    - S138: MethodTooBigCheck
    - S1444: PublicStaticFieldShouldBeFinalCheck (Python equivalent)
    - S1448: TooManyMethodsCheck
    """

    def __init__(
        self,
        class_name_format: str = r"^[A-Z][a-zA-Z0-9]*$",
        method_name_format: str = r"^[a-z_][a-z0-9_]*$",
        max_method_lines: int = 75,
        maximum_method_threshold: int = 35,
        count_non_public: bool = True,
    ):
        self.class_name_pattern = re.compile(class_name_format)
        self.method_name_pattern = re.compile(method_name_format)
        self.max_method_lines = max_method_lines
        self.maximum_method_threshold = maximum_method_threshold
        self.count_non_public = count_non_public

    def analyze_repository(self, repo_path: str) -> Dict:
        root = Path(repo_path)
        if not root.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        issues: List[RuleIssue] = []
        metrics = {
            "python_files": 0,
            "classes": 0,
            "methods": 0,
            "lines": 0,
        }

        for py_file in self._iter_python_files(root):
            metrics["python_files"] += 1
            file_issues, file_metrics = self._analyze_file(py_file, root)
            issues.extend(file_issues)
            for key in metrics:
                if key in file_metrics:
                    metrics[key] += file_metrics[key]

        return {
            "metrics": metrics,
            "issues": [asdict(issue) for issue in issues],
            "issues_count": len(issues),
        }

    def _iter_python_files(self, root: Path):
        excluded_dirs = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            "node_modules",
        }

        for file_path in root.rglob("*.py"):
            relative_parts = file_path.relative_to(root).parts
            if any(part in excluded_dirs for part in relative_parts):
                continue
            yield file_path

    def _analyze_file(self, file_path: Path, repo_root: Path) -> Tuple[List[RuleIssue], Dict]:
        relative_file = file_path.relative_to(repo_root).as_posix()
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        source_lines = source.splitlines()

        file_metrics = {
            "classes": 0,
            "methods": 0,
            "lines": len(source_lines),
        }

        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            return [
                RuleIssue(
                    rule_key="PY-SYNTAX",
                    file_path=relative_file,
                    line=error.lineno or 1,
                    message=f"Syntax error during analysis: {error.msg}",
                    severity="CRITICAL",
                    metric_name="SYNTAX_ERROR",
                    textRange={
                        "startLine": error.lineno or 1,
                        "endLine": error.lineno or 1,
                    },
                )
            ], file_metrics

        visitor = _RulesVisitor(
            file_path=relative_file,
            source_lines=source_lines,
            class_name_pattern=self.class_name_pattern,
            method_name_pattern=self.method_name_pattern,
            max_method_lines=self.max_method_lines,
            maximum_method_threshold=self.maximum_method_threshold,
            count_non_public=self.count_non_public,
        )
        visitor.visit(tree)

        file_metrics["classes"] = visitor.total_classes
        file_metrics["methods"] = visitor.total_methods

        return visitor.issues, file_metrics


class _RulesVisitor(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
        source_lines: List[str],
        class_name_pattern: re.Pattern,
        method_name_pattern: re.Pattern,
        max_method_lines: int,
        maximum_method_threshold: int,
        count_non_public: bool,
    ):
        self.file_path = file_path
        self.source_lines = source_lines
        self.class_name_pattern = class_name_pattern
        self.method_name_pattern = method_name_pattern
        self.max_method_lines = max_method_lines
        self.maximum_method_threshold = maximum_method_threshold
        self.count_non_public = count_non_public

        self.issues: List[RuleIssue] = []
        self.total_classes = 0
        self.total_methods = 0
        self.class_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_depth += 1
        self.total_classes += 1

        # Rule S101 (BadClassNameCheck): class naming convention.
        # S101 equivalent: class naming convention.
        if not self.class_name_pattern.fullmatch(node.name):
            self.issues.append(
                RuleIssue(
                    rule_key="S101",
                    file_path=self.file_path,
                    line=node.lineno,
                    message=(
                        f"Rename this class name to match the regular expression "
                        f"'{self.class_name_pattern.pattern}'."
                    ),
                    symbol_name=node.name,
                    metric_name="LEXIC CLASSNAME",
                    textRange={
                        "startLine": node.lineno,
                        "endLine": node.lineno,
                    },
                )
            )

        class_methods = [
            item
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.total_methods += len(class_methods)

        # Rule S1448 (TooManyMethodsCheck): too many methods in one class.
        # S1448 equivalent: too many methods in one class.
        methods_for_count = class_methods
        if not self.count_non_public:
            methods_for_count = [m for m in class_methods if not m.name.startswith("_")]

        if len(methods_for_count) > self.maximum_method_threshold:
            visibility_text = "" if self.count_non_public else " public"
            self.issues.append(
                RuleIssue(
                    rule_key="S1448",
                    file_path=self.file_path,
                    line=node.lineno,
                    message=(
                        f"Class '{node.name}' has {len(methods_for_count)}{visibility_text} methods, "
                        f"which is greater than the {self.maximum_method_threshold} authorized. "
                        "Split it into smaller classes."
                    ),
                    symbol_name=node.name,
                    metric_name="NMD VERY_HIGH",
                    textRange={
                        "startLine": node.lineno,
                        "endLine": getattr(node, "end_lineno", node.lineno),
                    },
                )
            )

        # Rule S1444 (PublicStaticFieldShouldBeFinalCheck): class attributes should be constants/Final.
        # S1444 equivalent for Python: class-level mutable/public-like attributes should be constants.
        for member in node.body:
            self._check_class_attribute_finality(member)

        # Rule S100 and Rule S138 are checked for each class method.
        for member in class_methods:
            self._check_method_rules(member)

        self.generic_visit(node)
        self.class_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Only check top-level functions here; methods are handled in visit_ClassDef.
        # Rule S100 and Rule S138 also apply to top-level functions.
        if self.class_depth == 0:
            self._check_function_name(node)
            self._check_method_too_big(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Rule S100 and Rule S138 also apply to top-level async functions.
        if self.class_depth == 0:
            self._check_function_name(node)
            self._check_method_too_big(node)
        self.generic_visit(node)

    def _check_method_rules(self, node: ast.AST):
        # Rule S100 (BadMethodNameCheck)
        self._check_function_name(node)
        # Rule S138 (MethodTooBigCheck)
        self._check_method_too_big(node)

    def _check_function_name(self, node: ast.AST):
        # Rule S100 (BadMethodNameCheck): function/method naming convention.
        name = getattr(node, "name", "")
        lineno = getattr(node, "lineno", 1)

        # Keep dunder methods excluded from naming checks.
        if name.startswith("__") and name.endswith("__"):
            return

        if not self.method_name_pattern.fullmatch(name):
            self.issues.append(
                RuleIssue(
                    rule_key="S100",
                    file_path=self.file_path,
                    line=lineno,
                    message=(
                        "Rename this method/function name to match the regular expression "
                        f"'{self.method_name_pattern.pattern}'."
                    ),
                    symbol_name=name,
                    metric_name="LEXIC METHODNAME",
                    textRange={
                        "startLine": lineno,
                        "endLine": lineno,
                    },
                )
            )

    def _check_method_too_big(self, node: ast.AST):
        # Rule S138 (MethodTooBigCheck): function/method exceeds authorized LOC.
        if not hasattr(node, "body") or not getattr(node, "body"):
            return

        block_start, block_end = self._get_block_line_range(node)
        if block_start is None or block_end is None:
            return

        lines_of_code = self._count_non_empty_non_comment_lines(block_start, block_end)
        if lines_of_code > self.max_method_lines:
            name = getattr(node, "name", "<unknown>")
            line = getattr(node, "lineno", 1)
            self.issues.append(
                RuleIssue(
                    rule_key="S138",
                    file_path=self.file_path,
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
            )

    def _check_class_attribute_finality(self, member: ast.stmt):
        # Rule S1444 (PublicStaticFieldShouldBeFinalCheck): class attributes should be constants/Final.
        if isinstance(member, ast.Assign):
            for target in member.targets:
                if isinstance(target, ast.Name):
                    self._emit_non_final_class_attribute_issue(target.id, target.lineno)
        elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
            target_name = member.target.id
            if self._annotation_contains_final(member.annotation):
                return
            self._emit_non_final_class_attribute_issue(target_name, member.lineno)

    def _emit_non_final_class_attribute_issue(self, name: str, line: int):
        # Rule S1444 issue emission.
        if name.startswith("__") and name.endswith("__"):
            return
        if name.isupper():
            return

        self.issues.append(
            RuleIssue(
                rule_key="S1444",
                file_path=self.file_path,
                line=line,
                message=f"Make this class attribute '{name}' a constant (UPPER_CASE) or Final.",
                symbol_name=name,
                metric_name="USE_GLOBAL_VARIABLE",
                textRange={
                    "startLine": line,
                    "endLine": line,
                },
            )
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

    def _count_non_empty_non_comment_lines(self, start_line: int, end_line: int) -> int:
        start_index = max(start_line - 1, 0)
        end_index = min(end_line, len(self.source_lines))

        loc = 0
        for line in self.source_lines[start_index:end_index]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                loc += 1
        return loc
