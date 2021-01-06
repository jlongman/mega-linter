import logging
import re
from enum import Enum

from megalinter.reporters.bb.line_parser import stdlint


class STATE(Enum):
    READY = 1
    LEVEL = 2
    FILE = 3
    LINE = 4
    REFERENCE = 5


class Parser(stdlint.Parser):
    ISSUES_FOUND = re.compile(r'\d+ issue\(s\) found:')
    LEVEL_PLUS_MESSAGE = re.compile(r'(Warning|Error|Notice): (.*)')
    ON_FILE_LINE = re.compile(r'on ((/?[a-zA-Z0-9-_.]+)+/?) line (\d+):')
    LINE_MESSAGE = re.compile(r'\d+: (.*)')
    REFERENCE_PLUS_LINK = re.compile(r'Reference: (https://github.com/terraform-linters/tflint/.*)')

    LEVEL_TABLE = {
        "Error": "HIGH",
        "Warning": "MEDIUM",
        "Notice": "LOW",
    }

    class Event:
        def __init__(self):
            self.file = None
            self.line = None
            self.level = None
            self.detail = None
            self.message = None
            self.link = None

    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)
        self.STATE = STATE.READY
        self.event = Parser.Event()

    def emit_event(self):
        if self.event.level is None:
            return None
        data = {
            "parser": self.linter,
            "file_type": self.file_type,
            "file": self.file,
        }
        if self.event.line is not None:
            data["line"] = int(self.event.line)
        if self.event.level is not None and self.event.level in Parser.LEVEL_TABLE.keys():
            data["level"] = Parser.LEVEL_TABLE[self.event.level]
            data["severity"] = data["level"]
        if self.event.message is not None:
            if self.event.detail is not None:
                data["message"] = f"{self.event.message}\n{self.event.detail}"
            else:
                data["message"] = self.event.message
        elif self.event.detail is not None:
            data["message"] = self.event.detail
        if self.event.link is not None:
            data["link"] = self.event.link
        self.event = Parser.Event()
        return data

    def process_line(self, raw_line):
        """
        :param raw_line:
        :return:
        """
        line = raw_line.strip()
        if line == "":
            return None

        logging.debug(f"[tflint line_parser] OK {self.STATE} {line}")
        event = None

        if re.fullmatch(Parser.ISSUES_FOUND, line):
            if self.STATE == STATE.READY:
                self.STATE = STATE.LEVEL
            else:
                event = self.lost(line)
        elif re.match(Parser.LEVEL_PLUS_MESSAGE, line):
            event = None
            if self.STATE == STATE.REFERENCE:
                event = self.emit_event()
                self.STATE = STATE.LEVEL
            if self.STATE == STATE.LEVEL:
                match = re.match(Parser.LEVEL_PLUS_MESSAGE, line)
                self.event.level = match.group(1)
                self.event.message = match.group(2)
                self.STATE = STATE.FILE
            else:
                event = self.lost(line)
        elif re.match(Parser.ON_FILE_LINE, line):
            if self.STATE == STATE.FILE:
                match = re.match(Parser.ON_FILE_LINE, line)
                self.event.file = match.group(1)
                self.event.line = match.group(3)
                self.STATE = STATE.LINE
            else:
                event = self.lost(line)
        elif re.match(Parser.LINE_MESSAGE, line):
            if self.STATE == STATE.LINE:
                match = re.match(Parser.LINE_MESSAGE, line)
                self.event.detail = match.group(1)
                self.STATE = STATE.REFERENCE
            else:
                event = self.lost(line)
        elif re.match(Parser.REFERENCE_PLUS_LINK, line):
            if self.STATE == STATE.REFERENCE:
                match = re.match(Parser.REFERENCE_PLUS_LINK, line)
                self.event.link = match.group(1)
                self.STATE = STATE.LEVEL
                event = self.emit_event()
        else:
            event = self.lost(line)
        return event

    def finished(self):
        self.STATE = STATE.READY
        return self.emit_event()

    def lost(self, line):
        # if self.STATE == STATE.READY:
        #     pass
        # elif self.STATE == STATE.LEVEL:
        #     pass
        # elif self.STATE == STATE.READY:
        #     pass
        # elif self.STATE == STATE.FILE:
        #     pass
        # elif self.STATE == STATE.READY:
        #     pass
        # elif self.STATE == STATE.REFERENCE:
        #     pass
        # return False
        return False


if __name__ == "__main__":
    import doctest

    # doctest.testmod()
    doctest.testfile("test/tflint.doctest")
