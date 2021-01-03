from megalinter.reporters.bb.line_parser import stdlint


class Parser(stdlint.Parser):
    def __init__(self, linter, file_type, file):
        stdlint.Parser.__init__(self, linter, file_type, file)

    def process_line(self, raw_line):
        if raw_line.startswith("Starting audit..."):
            return None
        elif raw_line.startswith("Audit done."):
            return None
        elif raw_line.startswith("Checkstyle ends with "):
            return None
        return super().process_line(raw_line[len("[ERROR] ") :])


if __name__ == "__main__":
    # run doctest by running : `python3 -m lib.bb.checkstyle`
    import doctest

    doctest.testfile("test/checkstyle.doctest")
