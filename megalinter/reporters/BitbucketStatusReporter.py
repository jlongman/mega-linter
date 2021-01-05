#!/usr/bin/env python3
"""
Bitbucket Status reporter
Post a Bitbucket status for each linter
No token API is required if the proxy is 'http://host.docker.internal:29418'
"""

import importlib
import logging

from megalinter import Reporter, config, utils
from megalinter.reporters.bb import bitbucket


def get_descriptions(linter):
    success_msg = "No errors were found in the linting process"
    error_not_blocking = "Errors were detected but are considered not blocking"
    error_msg = "Errors were detected, please view logs"

    if linter.status == "success" and linter.return_code == 0:
        description = success_msg
        result = "PASSED"
        safe = True
    elif linter.status == "error" and linter.return_code == 0:
        description = error_not_blocking
        result = "FAILED"
        safe = True
    else:
        description = error_msg
        result = "FAILED"
        safe = False
    if linter.show_elapsed_time is True:
        description += f" ({str(round(linter.elapsed_time_s, 2))}s)"
    return result, safe


##
# BB can only have 10 reports
# collect stats for pass and fail separately
# todo this isn't the right axis
class Overview:
    def __init__(self):
        self.seen = {"": 0}
        self.linter_pass_count = 0
        self.linter_pass_duration = 0
        self.linter_fail_count = 0
        self.errors_count = 0


# wrap the logging and warning around the bitbucketapi coherently.
def deco(func):
    def inner_function(*args, **kwargs):
        self = args[0]
        try:
            response = func(*args, **kwargs)
            if response is None:
                logging.warning(
                    f"[Bitbucket Status Reporter] {func.__name__} - None response"
                )
                return
            if 200 <= response.status_code < 299:
                logging.debug(
                    f"Successfully posted Bitbucket Status for {self.master.descriptor_id} "
                    f"with {self.master.linter_name}"
                )
            else:
                logging.warning(
                    f"[Bitbucket Status Reporter] {func.__name__} - Error posting Status for {self.master.descriptor_id} "
                    f"with {self.master.linter_name}: {response.status_code}\n"
                    f"Bitbucket API response: {response.text}"
                )
        except ConnectionError as e:
            logging.warning(
                f"[Bitbucket Status Reporter] {func.__name__} Error putting Status for {self.master.descriptor_id} "
                f"with {self.master.linter_name}: Connection error {str(e)}"
            )
        except Exception as e:
            logging.warning(
                f"[Bitbucket Status Reporter] {func.__name__} Error putting Status for {self.master.descriptor_id} "
                f"with {self.master.linter_name}: Error {str(e)}"
            )
            raise e

    return inner_function


class BitbucketStatusReporter(Reporter):
    overview = Overview()

    name = "BITBUCKET_STATUS"
    scope = "linter"

    def __init__(self, params=None):
        # Activate Bitbucket Status by default
        self.is_active = True
        super().__init__(params)

    def manage_activation(self):
        # Disable status for each linter if MULTI_STATUS is 'false'
        if config.exists("MULTI_STATUS") and config.get("MULTI_STATUS") == "false":
            self.is_active = False
        else:
            self.is_active = (
                config.exists("BITBUCKET_CLONE_DIR")
                and config.exists("BITBUCKET_REPO_OWNER")
                and config.exists("BITBUCKET_REPO_SLUG")
                and config.exists("BITBUCKET_COMMIT")
            )

    @deco
    def annotate_batch(self, report_name, this_count, events):
        bitbucket.annotate_batch(report_name, this_count, events)

    @deco
    def annotate_single(self, report_name, this_count, event):
        bitbucket.annotate_single(report_name, this_count, event)

    def add_report_item(self, file, status_code, stdout, index, fixed=False):
        linter = self.master
        if linter.linter_name not in BitbucketStatusReporter.overview.seen:
            BitbucketStatusReporter.overview.seen[linter.linter_name] = (len(BitbucketStatusReporter.overview.seen) + 1) * 1000

        if status_code > 0:
            report_name = "mega-linter"
            if config.get('BITBUCKET_SEPARATE_REPORTS', 'false') == 'true':
                report_name = f"{report_name}-${linter.linter_name}"

            if len(linter.file_extensions) > 0:
                file_type = linter.file_extensions[0].replace(".", "")
            else:
                file_type = ""
            # todo I forget how file_type is used, it may be better to rsplit
            try:
                parser = self.init_output_parser().Parser(
                    linter.linter_name, file_type, utils.remove_workspace(file)
                )
                annotations = parser.parse(stdout)
                if linter.number_errors > 0:
                    BitbucketStatusReporter.overview.seen[linter.linter_name] += len(annotations)
                    message = f"Processing {linter.linter_name} - {linter.number_errors} for {len(linter.files)}"
                    self.submit_report(
                        message, "PENDING", False, linter.elapsed_time_s, report_name, linter.linter_name
                    )
                self.annotate_batch(
                    report_name, BitbucketStatusReporter.overview.seen[linter.linter_name], annotations
                )

                logging.debug(
                    f"[bitbucket api] reported {linter.number_errors} annotations"
                )
            except Exception as e:
                logging.warning(
                    f"[bitbucket api] skipping {linter.linter_name} - error parsing report items: {e}"
                )

    def produce_report(self):
        if (
            config.exists("BITBUCKET_REPO_OWNER")
            and config.exists("BITBUCKET_REPO_SLUG")
            and config.exists("BITBUCKET_COMMIT")
        ):
            linter = self.master
            if linter.is_active:
                if linter.cli_lint_mode == "project":
                    found = "the project"
                else:
                    found = f"{len(linter.files)} files"
                errors = str(linter.number_errors)
                BitbucketStatusReporter.overview.linter_pass_count += 1
                BitbucketStatusReporter.overview.linter_pass_duration += linter.elapsed_time_s
                report_name = "mega-linter"
                sub_report_name = None
                if config.get('BITBUCKET_SEPARATE_REPORTS', 'false') == 'true':
                    result, safe = get_descriptions(self.master)
                    if linter.number_errors == 0:
                        elapsed_time = BitbucketStatusReporter.overview.linter_pass_duration
                        linter_count = BitbucketStatusReporter.overview.linter_pass_count
                        message = f"{linter_count} linters succeeded on {found}"
                        sub_report_name = "pass"
                    else:
                        elapsed_time = linter.elapsed_time_s
                        total_errors = BitbucketStatusReporter.overview.errors_count
                        message = f"This linter found problems in {errors}/{total_errors} for {found}"
                        sub_report_name = linter.linter_name
                    report_name = f"{report_name}-{sub_report_name}"
                else:
                    elapsed_time = BitbucketStatusReporter.overview.linter_pass_duration
                    total_errors = BitbucketStatusReporter.overview.errors_count
                    safe = total_errors == 0
                    result = (
                        "PASSED"
                        if safe
                        else
                        "FAILED"
                    )
                    message = f"Mega linter found problems in {total_errors} for {found}"
                self.submit_report(message, result, safe, elapsed_time, report_name, sub_report_name)

                if linter.number_errors == 0:
                    # produce the pass report - collects the linters which pass
                    self.annotate_linter_pass(sub_report_name)
                else:
                    pass  # todo
            else:
                pass
        else:
            logging.debug(
                f"Skipped post of Bitbucket Status for {self.master.descriptor_id} with {self.master.linter_name}"
            )

    def annotate_linter_pass(self, suffix=None):
        linter = self.master
        report_name = "mega-linter"
        if suffix is not None:
            report_name = f"{report_name}-{suffix}"
        total_linters = (
            BitbucketStatusReporter.overview.linter_fail_count
            + BitbucketStatusReporter.overview.linter_pass_count
        )
        summary = f"{linter.linter_name} found no errors on {len(linter.files)} files with {linter.file_extensions} extensions"
        if len(linter.file_extensions) > 0:
            file_type = linter.file_extensions[0].replace(".", "")
        else:
            file_type = ""
        event = {
            "parser": "pass",
            "file_type": file_type,
            "result": "PASSED",
            "summary": summary,
            "message": summary,
            "duration": linter.elapsed_time_s,
            "safe": True,
        }
        self.annotate_single(report_name, total_linters, event)

    @deco
    def submit_report(self, message, result, safe, duration, report_name, linter_name):
        if not linter_name:
            reporter = report_name
            title = "Mega-Linter scan report"
        else:
            reporter = linter_name
            title = f"Mega-Linter {reporter} scan report"
        data = {
            "title": title,
            "details": message,
            "report_type": "BUG",
            "reporter": reporter,
            "result": result,
            "data": [
                {"title": "Safe to merge?", "type": "BOOLEAN", "value": safe},
            ],
        }
        if duration is not None:
            data["data"].append({"title": "Duration (seconds)", "type": "DURATION", "value": duration}, )
        bitbucket.report(report_name, data)

    def init_output_parser(self):
        try:
            linter_name = self.master.linter_name.replace("-", "")
            mod = importlib.import_module(
                f"megalinter.reporters.bb.line_parser.{linter_name}"
            )
        # except ModuleNotFoundError:
        #     mod = importlib.import_module("{}.{}".format('bb', 'bbdefault'))
        finally:
            pass
        return mod
