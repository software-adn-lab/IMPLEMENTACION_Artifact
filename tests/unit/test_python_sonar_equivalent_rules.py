import tempfile
import unittest
from pathlib import Path

from models.PythonSonarEquivalentRules import PythonSonarEquivalentRules


class TestPythonSonarEquivalentRules(unittest.TestCase):
    def test_analyze_repository_generates_expected_issue(self):
        source = """
class TinyClass:
    def run(self):
        return 1
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "module_a.py").write_text(source, encoding="utf-8")

            analyzer = PythonSonarEquivalentRules()
            result = analyzer.analyze_repository(str(repo_path))

        issues = result["issues"]
        rule_keys = {issue["rule_key"] for issue in issues}

        self.assertIn("NEW-NMD-VERY-LOW", rule_keys)
        self.assertEqual(result["metrics"]["python_files"], 1)
        self.assertGreaterEqual(result["metrics"]["classes"], 1)

    def test_analyze_repository_raises_value_error_for_missing_path(self):
        analyzer = PythonSonarEquivalentRules()

        with self.assertRaises(ValueError):
            analyzer.analyze_repository("this_path_does_not_exist_123")

    def test_analyze_repository_reports_syntax_errors(self):
        bad_source = "def broken(:\n    pass\n"

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "broken.py").write_text(bad_source, encoding="utf-8")

            analyzer = PythonSonarEquivalentRules()
            result = analyzer.analyze_repository(str(repo_path))

        issue_keys = {issue["rule_key"] for issue in result["issues"]}
        self.assertIn("PY-SYNTAX", issue_keys)


if __name__ == "__main__":
    unittest.main()
