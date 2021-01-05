import io
import logging

from megalinter.reporters.bb.line_parser import lint2bb_parser

# lookup table
levels = {"warning": "MEDIUM", "error": "HIGH"}


def get_level(level):
    try:
        return levels[level]
    except KeyError:
        return "HIGH"


class Parser(lint2bb_parser):
    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)

    def parse(self, stdout):
        errors = []
        messages = io.StringIO(stdout)
        raw_line = messages.readline()
        if raw_line.strip() is self.file:
            # dedup
            raw_line = messages.readline()
        import sys

        while raw_line != "":
            raw_line = raw_line.strip()
            logging.debug(raw_line)
            if raw_line == "":
                raw_line = messages.readline()
                continue
            parse_line = raw_line.split(None, 2)
            if len(parse_line) >= 3:
                # print(parse_line)
                line, column = parse_line[0].split(":")
                level = parse_line[1]
                message = parse_line[2]
                errors.append(
                    {
                        "parser": self.linter,
                        "file_type": self.file_type,
                        "file": self.file,
                        "line": int(line),
                        "column": int(column),
                        "level": level,
                        "message": message,
                        "summary": message,
                        "severity": get_level(level),
                        "result": "FAILED",
                    }
                )
            # else:
            #     print(parse_line)
            #     print(raw_line)
            raw_line = messages.readline()

        return errors
