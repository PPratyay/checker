import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("coding-guidelines-checker.py")
SPEC = importlib.util.spec_from_file_location("coding_guidelines_checker", MODULE_PATH)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


BANNERS = {
    "include": "Include Files",
    "external_prototype": "Function Declarations",
    "function_definition": "Function Definitions",
}


def banner(title: str) -> str:
    return "/* ============================================================================ */\n/*                              " + title + "                              */\n/* ============================================================================ */\n"


class CheckerTests(unittest.TestCase):
    def run_check(self, text: str, suffix: str = ".c"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ("fixture" + suffix)
            path.write_text(text, encoding="utf-8")
            return checker.check_file(path)

    def test_valid_c_layout_and_banners(self):
        source = (
            "/* File header */\n"
            + banner(BANNERS["include"])
            + "#include <stddef.h>\n"
            + banner(BANNERS["external_prototype"])
            + "void run(void);\n"
            + banner(BANNERS["function_definition"])
            + "void run(void) { return; }\n"
        )
        self.assertEqual(self.run_check(source), [])

    def test_permuted_order_reports_include_at_its_line(self):
        source = (
            "/* File header */\n"
            + banner(BANNERS["function_definition"])
            + "void run(void) {}\n"
            + banner(BANNERS["include"])
            + "#include <stddef.h>\n"
        )
        findings = self.run_check(source)
        self.assertTrue(any(f.line == 9 and "Include Files" in f.message for f in findings))
        self.assertTrue(any("after Function Definitions" in f.message for f in findings))

    def test_wrong_banner_is_reported(self):
        source = (
            "/* File header */\n"
            + banner("Function Definitions")
            + "#include <stddef.h>\n"
        )
        findings = self.run_check(source)
        self.assertTrue(any("should be below 'Include Files'" in f.message for f in findings))

    def test_write_comments_embeds_and_does_not_duplicate(self):
        source = (
            "/* File header */\n"
            + banner(BANNERS["function_definition"])
            + "void run(void) {}\n"
            + banner(BANNERS["include"])
            + "#include <stddef.h>\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.c"
            path.write_text(source, encoding="utf-8")
            findings = checker.check_file(path)
            checker.write_review_comments(path, findings)
            annotated = path.read_text(encoding="utf-8")
            self.assertIn("/* review-comment -- Include Files 'stddef.h' is after", annotated)
            self.assertIn("come first */\n#include <stddef.h>", annotated)
            checker.write_review_comments(path, checker.check_file(path))
            self.assertEqual(annotated, path.read_text(encoding="utf-8"))

    def test_new_rules_accept_compliant_code(self):
        source = (
            "/* File header */\n"
            "#define VALUE 4\n"
            "int calculate(int left, int right)\n"
            "{\n"
            "    return (left + right) * (left - right);\n"
            "}\n"
            "void update(int *value)\n"
            "{\n"
            "    (*value)++;\n"
            "    return;\n"
            "}\n"
        )
        findings = self.run_check(source)
        self.assertFalse(any("complex expression" in f.message for f in findings))
        self.assertFalse(any("increment/decrement" in f.message for f in findings))
        self.assertFalse(any("return" in f.message for f in findings))

    def test_new_rules_report_expression_and_increment_violations(self):
        source = (
            "/* File header */\n"
            "int calculate(int a, int b, int c)\n"
            "{\n"
            "    return a + b * c;\n"
            "}\n"
            "void update(int *value)\n"
            "{\n"
            "    *value = (*value)++;\n"
            "    return;\n"
            "}\n"
        )
        findings = self.run_check(source)
        self.assertTrue(any("complex expression" in f.message for f in findings))
        self.assertTrue(any("increment/decrement" in f.message for f in findings))

    def test_new_rules_report_preprocessor_and_return_violations(self):
        source = (
            "/* File header */\n"
            " #define INDENTED 1\n"
            "int choose(int value)\n"
            "{\n"
            "    if (value) return 1;\n"
            "    return 0;\n"
            "}\n"
            "void finish(void)\n"
            "{\n"
            "    value = 1;\n"
            "}\n"
        )
        findings = self.run_check(source)
        self.assertTrue(any("preprocessor directive" in f.message for f in findings))
        self.assertTrue(any("multiple return" in f.message for f in findings))
        self.assertTrue(any("void function 'finish'" in f.message for f in findings))


if __name__ == "__main__":
    unittest.main()
