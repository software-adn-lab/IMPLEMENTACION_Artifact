import unittest

from controllers.main_controller import _map_local_rule_issue_to_moha


class TestMainControllerMapping(unittest.TestCase):
    def test_map_new_ninterf_rule_to_mi(self):
        rule_issue = {
            "rule_key": "NEW-NINTERF-VERY-HIGH",
            "metric_name": "NINTERF VERY_HIGH",
            "line": 10,
            "severity": "MAJOR",
            "file_path": "src/service.py",
            "textRange": {"startLine": 10, "endLine": 18},
        }

        mapped = _map_local_rule_issue_to_moha(rule_issue, "owner_repo")

        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["moha_smell"], "MI")
        self.assertEqual(mapped[0]["source"], "local")
        self.assertEqual(mapped[0]["project"], "owner_repo")

    def test_ignore_unknown_rule_key(self):
        rule_issue = {
            "rule_key": "NEW-UNKNOWN-RULE",
            "metric_name": "UNKNOWN METRIC",
            "line": 3,
            "severity": "MAJOR",
            "file_path": "src/unknown.py",
        }

        mapped = _map_local_rule_issue_to_moha(rule_issue, "owner_repo")

        self.assertEqual(mapped, [])


if __name__ == "__main__":
    unittest.main()
