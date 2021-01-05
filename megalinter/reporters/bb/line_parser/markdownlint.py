from megalinter.reporters.bb.line_parser import stdlint

# docker run -v $PWD/.:/tmp/lint -e RUN_LOCAL=true -eVALIDATE_MD=true  --rm -it jlongman/super-linter:stable
# ERROR:[/tmp/lint/README.md:5:69 MD009/no-trailing-spaces Trailing spaces [Expected: 0 or 2; Actual: 1]
# /tmp/lint/README.md:15:23 MD009/no-trailing-spaces Trailing spaces [Expected: 0 or 2; Actual: 1]
# /tmp/lint/README.md:26:43 MD009/no-trailing-spaces Trailing spaces [Expected: 0 or 2; Actual: 1]
# /tmp/lint/README.md:29:42 MD009/no-trailing-spaces Trailing spaces [Expected: 0 or 2; Actual: 1]


class Parser(stdlint.Parser):
    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)
