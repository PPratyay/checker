"""Check C/C++ coding guidelines and optionally embed review comments in source files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Iterable

from clang import cindex


SECTION_TITLES = {
    "include_guard": "Include Guard",
    "include": "Include Files",
    "macro": "Macros",
    "typedef": "Typedefs",
    "structure": "Structure Declarations",
    "external_variable": "Extern Variables",
    "static_variable": "Static Variables",
    "external_prototype": "Function Declarations",
    "static_prototype": "Static Function Prototypes",
    "function_definition": "Function Definitions",
    "static_function_definition": "Static Function Definitions",
}

# Required order is deliberately separate for C and header files.
C_ORDER = ("file_header", "include", "macro", "typedef", "structure", "external_variable", "static_variable", "external_prototype", "static_prototype", "function_definition", "static_function_definition")
HEADER_ORDER = ("file_header", "include_guard", "include", "macro", "typedef", "structure", "external_variable", "static_variable", "external_prototype", "static_prototype")

_BANNER_LINE = re.compile(r"^\s*/\*\s*(?P<fill>=+)\s*\*/\s*$")
_BANNER_TITLE = re.compile(r"^\s*/\*\s*(?P<title>[^*]+?)\s*\*/\s*$")
_HEADER_COMMENT = re.compile(r"^\s*(?://|/\*|\*)")
_GUARD = re.compile(r"^\s*#\s*(if\s*!defined|ifndef)\b", re.IGNORECASE)
_GUARD_NAME = re.compile(r"^\s*#\s*(?:if\s*!defined|ifndef)\s*[ (]*([A-Za-z_]\w*)", re.IGNORECASE)
_DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.line}: review comment: {self.message}"


@dataclass(frozen=True)
class Item:
    section: str
    line: int
    name: str


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    line: int
    end_line: int
    return_type: str


def _line_number(location: cindex.SourceLocation) -> int:
    return int(location.line or 1)


def _include_guard_names(lines: list[str]) -> set[str]:
    names: set[str] = set()
    for index, line in enumerate(lines):
        guard_match = _GUARD_NAME.match(line)
        if not guard_match:
            continue
        guard_name = guard_match.group(1)
        for following_line in lines[index + 1:index + 4]:
            define_match = _DEFINE.match(following_line)
            if define_match and define_match.group(1) == guard_name:
                names.add(guard_name)
                break
    return names


def _cursor_items(tu: cindex.TranslationUnit, source: Path, ignored_macros: set[str]) -> list[Item]:
    items: list[Item] = []
    source_name = str(source.resolve())
    for cursor in tu.cursor.get_children():
        if not cursor.location.file or str(Path(cursor.location.file.name).resolve()) != source_name:
            continue
        line = _line_number(cursor.location)
        name = cursor.spelling or cursor.displayname or "unnamed declaration"
        kind = cursor.kind
        if kind == cindex.CursorKind.INCLUSION_DIRECTIVE:
            items.append(Item("include", line, name))
        elif kind == cindex.CursorKind.MACRO_DEFINITION:
            if name in ignored_macros:
                continue
            items.append(Item("macro", line, name))
        elif kind == cindex.CursorKind.FUNCTION_DECL:
            if cursor.is_definition():
                section = "static_function_definition" if cursor.storage_class == cindex.StorageClass.STATIC else "function_definition"
                items.append(Item(section, line, name))
            elif cursor.storage_class == cindex.StorageClass.STATIC:
                items.append(Item("static_prototype", line, name))
            else:
                items.append(Item("external_prototype", line, name))
        elif kind == cindex.CursorKind.VAR_DECL:
            section = "static_variable" if cursor.storage_class == cindex.StorageClass.STATIC else "external_variable"
            items.append(Item(section, line, name))
        elif kind == cindex.CursorKind.TYPEDEF_DECL:
            items.append(Item("typedef", line, name))
        elif kind in (cindex.CursorKind.STRUCT_DECL, cindex.CursorKind.UNION_DECL, cindex.CursorKind.ENUM_DECL):
            if cursor.is_definition() or cursor.spelling:
                items.append(Item("structure", line, name))
    return sorted(items, key=lambda item: (item.line, item.section))


def _function_infos(tu: cindex.TranslationUnit, source: Path) -> list[FunctionInfo]:
    source_name = str(source.resolve())
    functions: list[FunctionInfo] = []
    for cursor in tu.cursor.walk_preorder():
        if cursor.kind != cindex.CursorKind.FUNCTION_DECL or not cursor.is_definition():
            continue
        if not cursor.location.file or str(Path(cursor.location.file.name).resolve()) != source_name:
            continue
        functions.append(FunctionInfo(
            cursor.spelling or "unnamed function",
            _line_number(cursor.location),
            int(cursor.extent.end.line or cursor.location.line),
            cursor.result_type.spelling,
        ))
    return functions


def _source_lines(source: Path) -> list[str]:
    return source.read_text(encoding="utf-8", errors="replace").splitlines()


def _file_header_line(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[:30], start=1):
        if line.strip() and not line.lstrip().startswith(("#", "//", "/*", "*", "*/")):
            break
        if _HEADER_COMMENT.match(line):
            return index
    return None


def _banner_for_line(lines: list[str], line: int) -> str | None:
    """Return the title of the nearest complete three-line banner above a line."""
    for end in range(line - 1, max(0, line - 8), -1):
        if end < 3:
            break
        first, title, last = lines[end - 3:end]
        if _BANNER_LINE.match(first) and _BANNER_TITLE.match(title) and _BANNER_LINE.match(last):
            match = _BANNER_TITLE.match(title)
            return re.sub(r"\s+", " ", match.group("title")).strip().lower() if match else None
    return None


def _banner_findings(lines: list[str], items: list[Item]) -> list[Finding]:
    findings: list[Finding] = []
    expected_titles = {title.lower() for title in SECTION_TITLES.values()}
    for item in items:
        title = _banner_for_line(lines, item.line)
        expected = SECTION_TITLES[item.section].lower()
        if title is None:
            findings.append(Finding(item.line, f"{item.section.replace('_', ' ')} '{item.name}' is not below a three-line '{SECTION_TITLES[item.section]}' section banner"))
        elif title not in expected_titles:
            findings.append(Finding(item.line, f"'{item.name}' is below an unrecognized section banner '{title}'"))
        elif title != expected:
            findings.append(Finding(item.line, f"{item.section.replace('_', ' ')} '{item.name}' is below '{title.title()}', but should be below '{SECTION_TITLES[item.section]}'"))
    return findings


def _layout_findings(lines: list[str], items: list[Item], is_header: bool) -> list[Finding]:
    order = HEADER_ORDER if is_header else C_ORDER
    rank = {section: index for index, section in enumerate(order)}
    findings: list[Finding] = []
    previous: Item | None = None
    for item in items:
        if item.section not in rank:
            continue
        if previous and rank[item.section] < rank[previous.section]:
            findings.append(Finding(item.line, f"{SECTION_TITLES[item.section]} '{item.name}' is after {SECTION_TITLES[previous.section]} '{previous.name}', but {SECTION_TITLES[item.section]} should come first"))
        previous = item

    header_line = _file_header_line(lines)
    if header_line is None:
        findings.append(Finding(1, "file header is missing at the top of the file"))
    elif items and header_line > items[0].line:
        findings.append(Finding(header_line, "file header appears after the first code section"))

    if is_header:
        guard_lines = [index for index, line in enumerate(lines, start=1) if _GUARD.match(line)]
        if not guard_lines:
            findings.append(Finding(1, "include guard is missing from the header file"))
        elif items and guard_lines[0] > items[0].line:
            findings.append(Finding(guard_lines[0], "include guard appears after the first code section"))
    return findings


def _code_line(line: str) -> str:
    line = re.sub(r"//.*$", "", line)
    return re.sub(r"/\*.*?\*/", "", line)


def _precedence_findings(lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    operators = re.compile(r"(?:&&|\|\||<<|>>|[+*/%&|^<>-])")
    for number, raw_line in enumerate(lines, start=1):
        line = _code_line(raw_line)
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.count("(") != line.count(")"):
            continue
        expression = line.split("=", 1)[1] if "=" in line and "==" not in line else line
        operator_count = len(operators.findall(expression))
        if operator_count >= 2 and expression.count("(") == 0:
            findings.append(Finding(number, "complex expression has multiple operators without explicit parentheses for precedence"))
    return findings


def _increment_findings(lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    increment = re.compile(r"\+\+|--")
    statement = re.compile(r"^\s*(?:\([^;]+\)|[A-Za-z_]\w*)\s*(?:\+\+|--)\s*;\s*$")
    for number, raw_line in enumerate(lines, start=1):
        line = _code_line(raw_line).strip()
        if not increment.search(line):
            continue
        if not statement.match(line):
            findings.append(Finding(number, "increment/decrement must be an isolated statement; do not combine it with other operators or expressions"))
    return findings


def _preprocessor_findings(lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for number, line in enumerate(lines, start=1):
        if re.match(r"\s+#", line):
            findings.append(Finding(number, "preprocessor directive must start at column 1"))
    return findings


def _function_exit_findings(lines: list[str], functions: list[FunctionInfo]) -> list[Finding]:
    findings: list[Finding] = []
    for function in functions:
        body = lines[function.line - 1:function.end_line]
        returns = [function.line + offset for offset, line in enumerate(body) if re.search(r"\breturn\b", _code_line(line))]
        if len(returns) > 1:
            findings.append(Finding(returns[1], f"function '{function.name}' has multiple return statements; use one return at the end"))
        if function.return_type == "void":
            if not returns:
                findings.append(Finding(function.end_line, f"void function '{function.name}' must end with an explicit return statement"))
            else:
                last_return = returns[-1]
                return_line = _code_line(lines[last_return - 1])
                trailing_text = return_line.split("return", 1)[1].split(";", 1)[1].strip()
                code_after_return = [
                    function.line + offset
                    for offset, line in enumerate(body)
                    if function.line + offset > last_return and _code_line(line).strip().strip("{};")
                ]
                if trailing_text.strip("{};") or code_after_return:
                    findings.append(Finding(last_return, f"void function '{function.name}' must have its explicit return statement at the end"))
    return findings


def check_file(source: Path, clang_args: Iterable[str] = ()) -> list[Finding]:
    lines = _source_lines(source)
    options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    index = cindex.Index.create()
    tu = index.parse(str(source), args=list(clang_args), options=options)
    items = _cursor_items(tu, source, _include_guard_names(lines))
    findings = _layout_findings(lines, items, source.suffix.lower() in {".h", ".hh", ".hpp", ".hxx"})
    findings.extend(_banner_findings(lines, items))
    functions = _function_infos(tu, source)
    findings.extend(_precedence_findings(lines))
    findings.extend(_increment_findings(lines))
    findings.extend(_preprocessor_findings(lines))
    findings.extend(_function_exit_findings(lines, functions))
    return sorted(set(findings), key=lambda finding: (finding.line, finding.message))


def check_category(source: Path, category: str, clang_args: Iterable[str] = ()) -> list[Finding]:
    """Run exactly one named guideline checker for a source file."""
    lines = _source_lines(source)
    options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    index = cindex.Index.create()
    tu = index.parse(str(source), args=list(clang_args), options=options)
    is_header = source.suffix.lower() in {".h", ".hh", ".hpp", ".hxx"}
    items = _cursor_items(tu, source, _include_guard_names(lines))
    if category == "U2_1_1":
        findings = _layout_findings(lines, items, is_header)
    elif category == "U2_1_2":
        findings = _banner_findings(lines, items)
    elif category == "U4_1_1":
        findings = _precedence_findings(lines)
    elif category == "U4_1_2":
        findings = _increment_findings(lines)
    elif category == "U4_2_1":
        findings = _preprocessor_findings(lines)
    elif category in {"U10_5_1", "U10_5_2"}:
        functions = _function_infos(tu, source)
        findings = _function_exit_findings(lines, functions)
        if category == "U10_5_1":
            findings = [finding for finding in findings if "multiple return" in finding.message]
        else:
            findings = [finding for finding in findings if "void function" in finding.message]
    else:
        raise ValueError(f"unknown rule category: {category}")
    return sorted(set(findings), key=lambda finding: (finding.line, finding.message))


def write_review_comments(source: Path, findings: list[Finding]) -> None:
    """Insert each finding above its original source line, without duplicates."""
    if not findings:
        return
    original_lines = source.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    comment_prefix = "/* review-comment -- "
    insertions: dict[int, list[str]] = {}
    for finding in findings:
        line_index = max(0, min(finding.line - 1, len(original_lines)))
        comment = comment_prefix + finding.message + " */"
        nearby = "".join(original_lines[max(0, line_index - 4):line_index])
        if comment in nearby:
            continue
        insertions.setdefault(line_index, []).append(comment + "\n")

    updated_lines: list[str] = []
    for index, line in enumerate(original_lines):
        updated_lines.extend(insertions.get(index, []))
        updated_lines.append(line)
    if len(original_lines) in insertions:
        updated_lines.extend(insertions[len(original_lines)])
    source.write_text("".join(updated_lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check C/C++ file layout and section banners.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--clang-arg", action="append", default=[], help="Argument passed to libclang; repeat as needed.")
    parser.add_argument("--write-comments", action="store_true", help="Embed review comments above violations in the source files.")
    args = parser.parse_args(argv)
    exit_code = 0
    for source in args.files:
        try:
            findings = check_file(source, args.clang_arg)
        except (OSError, cindex.LibclangError) as error:
            print(f"{source}: error: {error}", file=sys.stderr)
            exit_code = 2
            continue
        if args.write_comments:
            try:
                write_review_comments(source, findings)
            except OSError as error:
                print(f"{source}: error writing review comments: {error}", file=sys.stderr)
                exit_code = 2
                continue
        else:
            for finding in findings:
                print(f"{source}:{finding}")
        exit_code = max(exit_code, min(len(findings), 1))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
