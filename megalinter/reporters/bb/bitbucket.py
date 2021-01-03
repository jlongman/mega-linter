#!/usr/bin/env python3
import logging
import sys

import requests
from megalinter import config

# event format
# {
#     'parser': '',
#     'file_type': '',
#     'file': '',
#     'result': 'PASSED',
#     'message': '',
#     'summary': '',
#     'detail: '',
#     'line': 0,
#     'column': 0,
#     'duration': 0,
#     'safe': False
# }


def report(report_name, report_data):
    return call_bitbucket("put", f"{get_report_url(report_name)}", report_data)


def annotate_single(report_name, this_count, event):
    document = get_annotation_document(event, this_count)
    annotation_url = f"{get_report_url(report_name)}/annotations/{this_count}"
    return call_bitbucket("put", annotation_url, document)


def annotate_batch(report_name, this_count, events):
    if len(events) > 0:
        group_annotation_url = get_report_url(report_name) + "/annotations"
        annotations = []
        for single_result in events:
            this_count += 1
            annotations.append(get_annotation_document(single_result, this_count))
        return call_bitbucket("post", group_annotation_url, annotations)
    return None


def get_annotation_document(data, this_count):
    detail = data["message"]
    if "summary" in data:
        if data["summary"] is None:
            summary = data["message"]
        else:
            summary = data["summary"]
    else:
        summary = data["message"]
    if len(summary) > 100:
        summary = "{}...".format(summary[:96])
    if len(detail) > 2000:
        detail = "{}...".format(detail[:1996])

    annotation = {
        "external_id": f'mega-{data["parser"]}-{data["file_type"]}-{this_count}',
        "title": f'{data["parser"]} - {data["file_type"]}',
        "summary": summary,
        "annotation_type": "BUG",
        "reporter": "megalint",
    }
    if "result" in data:
        annotation["result"] = data["result"]
    if "file" in data:
        annotation["path"] = data["file"]
    if summary != detail:  # only add detail when necessary
        annotation["details"] = detail
    if "line" in data:
        if isinstance(data["line"], int) and int(data["line"]) > 0:
            annotation["line"] = data["line"]
        else:
            logging.warning(
                f"[bitbucket api] Unexpected data['line']: {data['line']}",
                file=sys.stderr,
            )
    if "column" in data:
        annotation["column"] = data["column"]
    if "safe" in data:
        safe = data["safe"]
    else:
        safe = False
    annotation["data"] = [{"title": "Safe to merge?", "type": "BOOLEAN", "value": safe}]
    if "duration" in data:
        annotation["data"].append(
            {"title": "Duration (s)", "type": "DURATION", "value": data["duration"]}
        )
    return annotation


def simple_report(report_name, count):
    good = count > 0
    if count > 0:
        failed = "FAILED"
    else:
        failed = "PENDING"
    return report(
        report_name, {"result": failed, "safe": good, "details": "na", "message": "na"}
    )


def call_bitbucket(verb, api_url, document):
    if config.get("BITBUCKET_COMMIT", "false") == "false":
        logging.warning(f"{verb} - {api_url}\r\n{document}")
        return None
    headers = {"content-type": "application/json"}
    proxies = {
        "http": "http://host.docker.internal:29418",
        "https": "http://host.docker.internal:29418",
    }

    if "put" == verb:
        response = requests.put(
            url=api_url, proxies=proxies, headers=headers, json=document
        )
        return response
    elif "post" == verb:
        response = requests.post(
            url=api_url, proxies=proxies, headers=headers, json=document
        )
        return response
    else:
        logging.warning(f"INTERNAL ERROR: INVALID METHOD {verb}", file=sys.stderr)
    return None


def get_report_url(report_name):
    bitbucket_repo_owner = config.get("BITBUCKET_REPO_OWNER")
    bitbucket_repo_slug = config.get("BITBUCKET_REPO_SLUG")
    bitbucket_api_url = config.get("BITBUCKET_API_URL", "http://api.bitbucket.org")
    bitbucket_commit = config.get("BITBUCKET_COMMIT")
    report_url = (
        f"{bitbucket_api_url}/2.0/repositories/{bitbucket_repo_owner}/{bitbucket_repo_slug}"
        f"/commit/{bitbucket_commit}/reports/{report_name}"
    )
    return report_url


# if __name__ == '__main__':
#     messages = sys.stdin
#     linter_name = messages.readline().strip()
#
#     print("linter {}".format(linter_name), file=sys.stderr)
#     file_type = messages.readline().strip()
#     file_name = messages.readline().strip()
#     count = int(messages.readline().strip())
#     print("file_name {}".format(file_name), file=sys.stderr)
#
#     invoke_bitbucket(linter_name, file_type, file_name, count)
