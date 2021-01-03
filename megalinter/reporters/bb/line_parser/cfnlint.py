import io

from megalinter.reporters.bb.line_parser import lint2bb_parser

ERROR_LEVEL = "MEDIUM"


class Parser(lint2bb_parser):
    def __init__(self, linter, file_type, file):
        lint2bb_parser.__init__(self, linter, file_type, file)

    def parse(self, stdout):
        messages = io.StringIO(stdout)

        errors = []
        raw_line = messages.readline()
        line = -1  # error case
        while raw_line != "":
            raw_line = raw_line.strip()
            # print(raw_line, file=sys.stderr)
            if raw_line == "":
                raw_line = messages.readline()
                continue
            rcolumn, rline, rmessage = raw_line[::-1].split(":", 2)
            message = rmessage[::-1]
            column = rcolumn[::-1]
            line = rline[::-1]
            event = self.to_event(message, None, line, column)
            errors.append(event)
            raw_line = messages.readline()

        return errors

    def to_event(self, last_message, summary, line, column):
        event = {
            "parser": self.linter,
            "file_type": self.file_type,
            "file": self.file,
            "line": int(line),
            "column": int(column),
            "level": ERROR_LEVEL,
            "severity": ERROR_LEVEL,
            "message": last_message,
        }
        if summary is not None:
            event["summary"] = summary
        return event


if __name__ == "__main__":
    import doctest

    doctest.testfile("test/cfnlint.doctest")
