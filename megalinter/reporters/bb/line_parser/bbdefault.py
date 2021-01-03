import io

from megalinter.reporters.bb.line_parser import lint2bb_parser

DEFAULT_ERROR_LEVEL = "MEDIUM"


class Parser(lint2bb_parser):
    def __init__(self, linter, file_type, file):
        lint2bb_parser.__init__(self, linter, file_type, file)

    def parse(self, stdout):
        messages = io.StringIO(stdout)
        return [self.to_event(messages, None)]

    def to_event(self, last_message, summary):
        read_message = last_message.read()
        event = {
            "parser": self.linter,
            "file_type": self.file_type,
            "file": self.file,
            "level": DEFAULT_ERROR_LEVEL,
            "severity": DEFAULT_ERROR_LEVEL,
            "message": read_message,
        }
        if summary is not None:
            event["summary"] = summary
        return event


if __name__ == "__main__":
    # run doctest by running : `python3 -m lib.bb.bbdefault`
    import doctest

    doctest.testfile("test/bbdefault.doctest")
