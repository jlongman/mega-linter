from megalinter.reporters.bb.line_parser import stdlint


class Parser(stdlint.Parser):
    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)
