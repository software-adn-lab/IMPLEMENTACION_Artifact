import unittest
from unittest.mock import Mock, patch

from models.JSONReader import JSONReader


class TestJSONReader(unittest.TestCase):
    @patch("models.JSONReader.requests.get")
    def test_get_report_code_smells_success(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "issues": [
                {
                    "rule": "python:S100",
                    "line": 7,
                    "severity": "MAJOR",
                    "component": "repo:src/file.py",
                    "key": "issue-1",
                    "project": "owner_repo",
                    "textRange": {"startLine": 7, "endLine": 7},
                }
            ]
        }
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        reader = JSONReader("owner_repo")
        reader.GetReportCodeSmells()
        issues = reader.extractCodeSmells()

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["rule"], "python:S100")
        self.assertEqual(issues[0]["component"], "src/file.py")

    @patch("models.JSONReader.requests.get")
    def test_get_report_code_smells_private_repo_error(self, mock_get):
        response = Mock()
        response.status_code = 401
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        reader = JSONReader("owner_repo")

        with self.assertRaises(Exception) as ctx:
            reader.GetReportCodeSmells()

        self.assertIn("private", str(ctx.exception).lower())

    @patch("models.JSONReader.requests.get")
    def test_get_report_code_smells_project_not_found_error(self, mock_get):
        response = Mock()
        response.status_code = 404
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        reader = JSONReader("owner_repo")

        with self.assertRaises(Exception) as ctx:
            reader.GetReportCodeSmells()

        self.assertIn("not found", str(ctx.exception).lower())

    def test_extract_code_smells_raises_when_no_data_loaded(self):
        reader = JSONReader("owner_repo")

        with self.assertRaises(Exception) as ctx:
            reader.extractCodeSmells()

        self.assertIn("private", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
