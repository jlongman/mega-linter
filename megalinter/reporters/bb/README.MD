# Bitbucket Development

## Local development

Most code can be simulated by setting these variables:
```shell
BITBUCKET_CLONE_DIR=$(workspace) # directory to be linted e.g. /tmp/lint
BITBUCKET_REPO_OWNER=anything
BITBUCKET_REPO_SLUG=anything
BITBUCKET_COMMIT=false
```

e.g. in docker you would use:
```shell
FLAVOR="" # ie all
FLAVOR="-ci_light"
VERSION="v4.20.0"
VERSION="test"
docker run --rm -it \
   -v "$(pwd)":/tmp/lint \
   --net host \
   -e BITBUCKET_CLONE_DIR=/tmp/lint \
   -e BITBUCKET_REPO_OWNER=mvcode \
   -e BITBUCKET_REPO_SLUG=fake \
   -e BITBUCKET_COMMIT=false \
   "jlongman/mega-linter$FLAVOR:$VERSION"
```

In this mode instead of hitting bitbucket it logs the calls to bitbucket without validation.  It will look like below:

Report:
```
2021-01-03 22:59:32,385 [WARNING] put - http://api.bitbucket.org/2.0/repositories/mvcode/fake/commit/false/reports/pass
{'title': 'Mega-Linter pass scan report', 'details': '2 linters succeeded on 12 files', 'report_type': 'BUG', '
reporter': 'mega-linter-pass', 'result': 'PASSED', '
data': [{'title': 'Duration (seconds)', 'type': 'DURATION', 'value': 13.242644500001916}, {'title': 'Safe to merge?', 'type': 'BOOLEAN', 'value': True}]
} 2021-01-03 22:59:32,385 [WARNING] [Bitbucket Status Reporter] submit_report - None response 2021-01-03 22:59:
```
Annotations
```
32,386 [WARNING] put - http://api.bitbucket.org/2.0/repositories/mvcode/fake/commit/false/reports/pass/annotations/2
{'external_id': 'mega-pass-json-2', 'title': 'pass - json', 'summary': "jsonlint good on 12 files with ['.json']
extensions", 'annotation_type': 'BUG', 'reporter': 'megalint', 'result': 'PASSED', 'details': '', '
data': [{'title': 'Safe to merge?', 'type': 'BOOLEAN', 'value': True}, {'title': 'Duration (s)', 'type': 'DURATION', 'value': 12.658937800006242}]
} 2021-01-03 22:59:32,386 [WARNING] [Bitbucket Status Reporter] annotate_single - None response
```

- reports conform to the bitbucket [report API](https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Bworkspace%7D/%7Brepo_slug%7D/commit/%7Bcommit%7D/reports/%7BreportId%7D), 
- annotations to the bitbucket [annotation API - batch](https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Bworkspace%7D/%7Brepo_slug%7D/commit/%7Bcommit%7D/reports/%7BreportId%7D/annotations) and [annotation API - single](https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Bworkspace%7D/%7Brepo_slug%7D/commit/%7Bcommit%7D/reports/%7BreportId%7D/annotations/%7BannotationId%7D)

Note this is a work in progress.

# Line parsers

Line parsers transform the error message into annotations for a report.  If line and possibly column information is available this will provide hotlinking and inline visibility of the linters error message.

Line parsers take the stdout of the linter and parse this to discover linter message, and if possible line and if possible column information.  These are transformed into an internal (ie non Bitbucket) well known structure to be sent to bitbucket APIs.

This is a rough idea of what this structure needs to look like:
```json
{
     "parser": "pylint",
     "file_type": "py",
     "file": "foo/bar.py",
     "result": "PASSED",
     "message": "unclear",
     "summary": "unclear",
     "detail": "unclear",
     "line": 1,
     "column": 0,
     "duration": 2,
     "safe": true
}
```

Note: `line`, `column`, `duration` are definitely optional. 

## writing a new line parser

Line parsers are discovered from the `linter_name`.  If the matching class doesn't exist the annotations are skipped.

The line parser class is defined in `line_parser/__init__.py` as `lint2bb_parser`:
```python
class lint2bb_parser:
    def __init__(self, linter, file_type, file):
        self.linter = linter
        self.file_type = file_type
        self.file = file

    def parse(self, messages):
        pass
```

Many parsers follow a variant of the `stdlint.py` parser and can either directly inherit from it or borrow parts from it.  See the other parsers for examples.
