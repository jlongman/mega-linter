from megalinter.reporters.bb.line_parser import stdlint


class Parser(stdlint.Parser):
    def __init__(self, linter, file_type, file):
        stdlint.Parser.__init__(self, linter, file_type, file)
