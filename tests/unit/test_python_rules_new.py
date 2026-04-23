import ast
import unittest

from models.python_rules.new_nacc_very_high_rule import NewNaccVeryHighRule
from models.python_rules.new_ninterf_very_high_rule import NewNinterfVeryHighRule
from models.python_rules.new_nmd_very_low_rule import NewNmdVeryLowRule
from models.python_rules.new_nprivfield_high_rule import NewNprivfieldHighRule


def _first_class_from_source(source: str) -> ast.ClassDef:
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef):
            return node
    raise AssertionError("Expected one class in source")


class TestNewRules(unittest.TestCase):
    def test_new_nacc_very_high_positive(self):
        source = """
class UserData:
    def __init__(self):
        self._a = 1
    def get_a(self):
        return self._a
    def get_b(self):
        return self._a
    def get_c(self):
        return self._a
    def get_d(self):
        return self._a
    def get_e(self):
        return self._a
    def process(self):
        return 1
"""
        node = _first_class_from_source(source)
        rule = NewNaccVeryHighRule(min_accessor_methods=5, min_accessor_ratio=0.66)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_key, "NEW-NACC-VERY-HIGH")

    def test_new_nacc_very_high_negative_when_ratio_is_low(self):
        source = """
class UserData:
    def __init__(self):
        self._a = 1
    def get_a(self):
        return self._a
    def get_b(self):
        return self._a
    def get_c(self):
        return self._a
    def get_d(self):
        return self._a
    def run_1(self):
        return 1
    def run_2(self):
        return 1
    def run_3(self):
        return 1
"""
        node = _first_class_from_source(source)
        rule = NewNaccVeryHighRule(min_accessor_methods=5, min_accessor_ratio=0.66)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 0)

    def test_new_nprivfield_high_positive(self):
        source = """
class BigState:
    def __init__(self):
        self._f1 = 1
        self._f2 = 2
        self._f3 = 3
        self._f4 = 4
        self._f5 = 5
        self._f6 = 6
        self._f7 = 7
        self._f8 = 8
"""
        node = _first_class_from_source(source)
        rule = NewNprivfieldHighRule(private_field_threshold=8)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_key, "NEW-NPRIVFIELD-HIGH")

    def test_new_nprivfield_high_negative_below_threshold(self):
        source = """
class BigState:
    def __init__(self):
        self._f1 = 1
        self._f2 = 2
        self._f3 = 3
        self._f4 = 4
        self._f5 = 5
        self._f6 = 6
        self._f7 = 7
"""
        node = _first_class_from_source(source)
        rule = NewNprivfieldHighRule(private_field_threshold=8)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 0)

    def test_new_nmd_very_low_positive(self):
        source = """
class TinyClass:
    def a(self):
        return 1
    def b(self):
        return 2
"""
        node = _first_class_from_source(source)
        rule = NewNmdVeryLowRule(min_methods_threshold=3)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_key, "NEW-NMD-VERY-LOW")

    def test_new_nmd_very_low_negative_above_threshold(self):
        source = """
class RichClass:
    def a(self):
        return 1
    def b(self):
        return 2
    def c(self):
        return 3
    def d(self):
        return 4
"""
        node = _first_class_from_source(source)
        rule = NewNmdVeryLowRule(min_methods_threshold=3)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 0)

    def test_new_ninterf_very_high_positive(self):
        source = """
class TypeDispatcher:
    def handle(self, obj):
        if isinstance(obj, int):
            return 1
        elif isinstance(obj, str):
            return 2
        else:
            return 3

    def convert(self, obj):
        if type(obj) is int:
            return "int"
        elif type(obj) is str:
            return "str"
        else:
            return "other"
"""
        node = _first_class_from_source(source)
        rule = NewNinterfVeryHighRule(min_type_branches=3, min_repeated_methods=2)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_key, "NEW-NINTERF-VERY-HIGH")

    def test_new_ninterf_very_high_negative_when_only_one_method_has_type_checks(self):
        source = """
class TypeDispatcher:
    def handle(self, obj):
        if isinstance(obj, int):
            return 1
        elif isinstance(obj, str):
            return 2
        else:
            return 3

    def convert(self, obj):
        return str(obj)
"""
        node = _first_class_from_source(source)
        rule = NewNinterfVeryHighRule(min_type_branches=3, min_repeated_methods=2)

        issues = rule.check_class(node, "sample.py")

        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
