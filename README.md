# Coding Guidelines Checker

A read-only checker for the C/C++ file layout and section-banner rules shown in the project guideline.

## Requirements

- Python 3.9+
- `libclang` (`pip install libclang`)

The checker uses libclang for declarations, definitions, includes, and macros. Regular expressions are used only for the exact three-line comment-banner shape because comments are not represented as declaration cursors.

## Usage

```powershell
python .\coding-guidelines-checker.py path\to\file.c path\to\file.h
```

Additional compiler arguments can be repeated:

```powershell
python .\coding-guidelines-checker.py src\driver.c --clang-arg=-Iinclude --clang-arg=-DPLATFORM_X
```

## Sample files

The `tests` folder contains ready-to-run examples:

```powershell
python .\coding-guidelines-checker.py .\tests\valid_example.c .\tests\valid_example.h
```

The valid examples should produce no output and exit with code `0`. To see review comments for violations, run:

```powershell
python .\coding-guidelines-checker.py .\tests\misordered_example.c .\tests\misordered_example.h
```

The invalid examples intentionally place sections in the wrong order. They should print findings and exit with code `1`.

Additional-rule fixtures are also available:

```powershell
python .\coding-guidelines-checker.py .\tests\additional_rules_valid.c
python .\coding-guidelines-checker.py .\tests\additional_rules_violations.c .\tests\additional_rules_violations.h
```

These cover explicit parentheses around multi-operator expressions, isolated `++`/`--` statements, preprocessor directives at column 1, a single return point, and explicit final returns from `void` functions.

## Rule-specific files

The `tests/rules` directory has one generated sample for each guideline:

- `U2_1_1_file_section_order.c` and `.h`: file section order
- `U2_1_2_code_section_banners.c`: section banner matching
- `U4_1_1_explicit_parentheses.c`: explicit parentheses for precedence
- `U4_1_2_isolated_increment.c`: isolated increment/decrement
- `U4_2_1_preprocessor_column.c`: preprocessor column alignment
- `U10_5_1_single_return.c`: single return point
- `U10_5_2_void_explicit_return.c`: explicit return in `void` functions

The samples were annotated by the checker itself with:

```powershell
$files = Get-ChildItem .\tests\rules -File | Select-Object -ExpandProperty FullName
python .\coding-guidelines-checker.py --write-comments $files
```

Each generated annotation has the form `/* review-comment -- explanation */` and is placed immediately above the violating source line.

To embed the review comments directly into the invalid files instead of printing findings, run:

```powershell
python .\coding-guidelines-checker.py --write-comments .\tests\misordered_example.c .\tests\misordered_example.h
```

This writes portable C comments immediately above each violation, for example `/* review-comment -- Include Files should come first */`. The command is silent about findings; exit code `1` means comments were added or already present for detected violations. Running it again does not duplicate comments.

Each finding is printed as:

```text
path\to\file.c:42: review comment: Include Files 'stdio.h' is after Function Definitions 'main', but Include Files should come first
```

Without `--write-comments`, the input files are never modified and findings are printed for dry-run review. With `--write-comments`, findings are embedded as `/* review-comment -- explanation */` immediately above the offending line. A non-zero exit status means at least one guideline finding was reported; `2` means the file could not be parsed, read, or updated.

## Enforced order

For `.c` files: file header, includes, macros, typedefs, structure declarations, external variables, static variables, external function prototypes, static function prototypes, external function definitions, and static function definitions.

For `.h`, `.hh`, `.hpp`, and `.hxx` files: file header, include guard, includes, macros, typedefs, structure declarations, external variables, static variables, external function prototypes, and static function prototypes.

The checker also enforces the guideline examples for expression and control-flow safety:

- Complex expressions with multiple operators must use explicit parentheses.
- Increment/decrement must be isolated statements; postfix use is accepted for a simple operand, while prefix use is rejected.
- Preprocessor directives must begin in column 1.
- Non-void functions must use one return statement at the end.
- `void` functions must have an explicit final `return;` statement.

The expression and statement checks are conservative source checks. libclang supplies function definitions, ranges, and declaration structure; regular expressions inspect operators, returns, increment/decrement statements, and preprocessor indentation.

Every detected code item must be below a complete three-line banner whose title matches its section, for example `Macros`, `Include Files`, or `Function Definitions`. The checker reports findings but does not attempt automatic fixes because moving declarations can change linkage, initialization order, macro visibility, and include dependencies.

## Tests

```powershell
python -m unittest -v
```
