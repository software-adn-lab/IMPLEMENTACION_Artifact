import unittest

from models.AntipatternDetector import DetectAntipattern


class TestAntipatternDetector(unittest.TestCase):
    def test_detect_blob_when_all_conditions_present(self):
        related_smells = [
            {"moha_smell": "LCS", "component": "src/a.py"},
            {"moha_smell": "CC", "component": "src/a.py"},
            {"moha_smell": "DC", "component": "src/a.py"},
        ]

        result = DetectAntipattern(related_smells)

        self.assertEqual(result["BLOB"]["condiciones_cumplidas"], 3)
        self.assertIn("detected", result["BLOB"]["detectado"].lower())
        self.assertEqual(len(result["BLOB"]["archivos_con_antipatron"]), 1)

    def test_no_detection_when_input_is_empty(self):
        result = DetectAntipattern([])

        for antipattern_name, antipattern_result in result.items():
            self.assertEqual(
                antipattern_result["condiciones_cumplidas"],
                0,
                msg=f"Unexpected conditions for {antipattern_name}",
            )
            self.assertIn("not detected", antipattern_result["detectado"].lower())

    def test_blob_likely_when_half_or_more_conditions(self):
        related_smells = [
            {"moha_smell": "LCS", "component": "src/a.py"},
            {"moha_smell": "CC", "component": "src/a.py"},
        ]

        result = DetectAntipattern(related_smells)

        self.assertEqual(result["BLOB"]["condiciones_cumplidas"], 2)
        self.assertIn("likely", result["BLOB"]["detectado"].lower())

    def test_blob_not_detected_when_less_than_half_conditions(self):
        related_smells = [
            {"moha_smell": "CC", "component": "src/a.py"},
        ]

        result = DetectAntipattern(related_smells)

        self.assertEqual(result["BLOB"]["condiciones_cumplidas"], 1)
        self.assertIn("not detected", result["BLOB"]["detectado"].lower())


if __name__ == "__main__":
    unittest.main()
