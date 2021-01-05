from megalinter.reporters.bb.line_parser import stdlint


class Parser(stdlint.Parser):

    def __init__(self, linter, file_type, file):
        super().__init__(linter, file_type, file)

    def process_line(self, raw_line):
        """

        :param raw_line:
        :return:

        >>> Parser("a","b","c").process_line('/tmp/lint/infrastructure/docker/maxwell/Dockerfile:11 DL3008 '\
        'Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install '\
        '<package>=<version>`')
        {'parser': 'a', 'file_type': 'b', 'file': 'c', 'line': 11, 'level': 'HIGH', 'message': \
'DL3008 Pin versions in apt get install. Instead of `apt-get install <package>` use `apt-get install \
<package>=<version>`', 'severity': 'HIGH'}
        >>> Parser("a","b","c").process_line("x:999 xxx")
        {'parser': 'a', 'file_type': 'b', 'file': 'c', 'line': 999, 'level': 'HIGH', 'message': \
'xxx', 'severity': 'HIGH'}
        >>> Parser("a","b","c").process_line("xxxxx")

        """
        return super().process_line(raw_line)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
