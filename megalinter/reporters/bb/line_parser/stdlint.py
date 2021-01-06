import io
import logging

from megalinter.reporters.bb.line_parser import lint2bb_parser


class Parser(lint2bb_parser):
    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)

    def parse(self, stdout):
        events = []
        messages = io.StringIO(stdout)
        raw_line = messages.readline()
        # if raw_line.strip() is self.file:
        #     # dedup
        #     raw_line = messages.readline()
        while raw_line != "":
            event = self.process_line(raw_line)
            if event is not None:
                events.append(event)
            raw_line = messages.readline()
        event = self.finished()
        if event is not None:
            events.append(event)
        return events

    def finished(self):
        return None

    def process_line(self, raw_line):
        """

        :param raw_line:
        :return:

        >>> Parser("a","b","c").process_line('/tmp/lint/README.md:29:42 MD009/no-trailing-spaces Trailing '\
'spaces [Expected: 0 or 2; Actual: 1]')
        {'parser': 'a', 'fileType': 'b', 'file': 'c', 'line': 29, 'level': 'HIGH', 'message': \
'MD009/no-trailing-spaces Trailing spaces [Expected: 0 or 2; Actual: 1]', 'severity': 'HIGH', 'column': 42}
        >>> Parser("a","b","c").process_line('/tmp/lint/README.md:5 MD025/single-title/single-h1 '\
    'Multiple top level headings in the same document [Context: "# CI Pipeline"]')
        {'parser': 'a', 'fileType': 'b', 'file': 'c', 'line': 5, 'level': 'HIGH', 'message': \
'MD025/single-title/single-h1 Multiple top level headings in the same document [Context: "# CI Pipeline"]'\
, 'severity': 'HIGH'}
        >>> Parser("a","b","c").process_line("x:999 xxx")
        {'parser': 'a', 'fileType': 'b', 'file': 'c', 'line': 999, 'level': 'HIGH', 'message': \
'xxx', 'severity': 'HIGH'}
        >>> Parser("a","b","c").process_line("xxxxx")
        skipping xxxxx
        """
        try:
            raw_line = raw_line.strip()
            # print(raw_line, file=sys.stderr)
            if self.has_column(raw_line):
                # we have a column
                file, line, parse_line = raw_line.split(":", 2)
                column, message = parse_line.split(" ", 1)
                if column.endswith(":"):
                    column = column[:-1]
            else:
                # we don't
                file, parse_line = raw_line.split(":", 1)
                line, message = parse_line.split(" ", 1)
                column = None

            data = {
                "parser": self.linter,
                "file_type": self.file_type,
                "file": self.file,
                "line": int(line),
                "level": "HIGH",
                "message": message,
                "severity": "HIGH",
                "result": "FAILED",
            }

            if column is not None:
                try:
                    data["column"] = int(column)
                except ValueError:
                    pass
            return data
        except ValueError as e:
            logging.debug(e)

            logging.debug(f"[stdlint bb line_parser] skipping \"{raw_line}\" due to {e}")
            return None
        except Exception as e:
            logging.error(e)

            logging.info(f"[stdlint bb line_parser] skipping \"{raw_line}\" due to {e}")
            return None

    @staticmethod
    def has_column(raw_line):
        first_colon = raw_line.index(":")
        try:
            first_space_after_first_colon = raw_line.index(" ", first_colon)
        except ValueError:
            first_space_after_first_colon = 9999999
        try:
            second_colon = raw_line.index(":", first_colon + 1)
        except ValueError:
            second_colon = 9999999 + 1
        has_column = second_colon < first_space_after_first_colon
        return has_column


if __name__ == "__main__":
    import doctest

    doctest.testmod()
