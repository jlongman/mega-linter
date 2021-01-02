#!/usr/bin/env python3
"""
Bitbucket Status reporter
Post a Bitbucket status for each linter
No token API is required if the proxy is 'http://host.docker.internal:29418'
"""
import logging

import requests

from megalinter import Reporter, config


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
        result = "PENDING"
        safe = True
    else:
        description = error_msg
        result = "FAILED"
        safe = False
    if linter.show_elapsed_time is True:
        description += f" ({str(round(linter.elapsed_time_s, 2))}s)"
    return result, safe


class BitbucketStatusReporter(Reporter):
    name = "BITBUCKET_STATUS"
    scope = "linter"

    bitbucket_api_url = "https://api.bitbucket.org"
    bitbucket_server_url = "https://bitbucket.org"

    def __init__(self, params=None):
        # Activate Bitbucket Status by default
        self.is_active = True
        super().__init__(params)

    def manage_activation(self):
        # Disable status for each linter if MULTI_STATUS is 'false'
        if config.exists("MULTI_STATUS") and config.get("MULTI_STATUS") == "false":
            self.is_active = False
        if not config.exists("BITBUCKET_CLONE_DIR"):
            self.is_active = False

    def produce_report(self):
        if (
            config.exists("BITBUCKET_REPO_OWNER")
            and config.exists("BITBUCKET_REPO_SLUG")
            and config.exists("BITBUCKET_COMMIT")
        ):
            bitbucket_repo_owner = config.get("BITBUCKET_REPO_OWNER")
            bitbucket_repo_slug = config.get("BITBUCKET_REPO_slug")
            bitbucket_repo = f"{bitbucket_repo_owner}/{bitbucket_repo_slug}"
            bitbucket_api_url = config.get("BITBUCKET_API_URL", self.bitbucket_api_url)
            sha = config.get("BITBUCKET_COMMIT")

            result, safe = get_descriptions(self.master)
            url = f"{bitbucket_api_url}/2.0/repositories/{bitbucket_repo}/commit/{sha}/reports/mega-linter"

            linter = self.master
            if linter.is_active:
                if linter.cli_lint_mode == "project":
                    found = "the project"
                    errors = (
                        str(linter.number_errors)
                        if linter.number_errors > 0
                        else "no"
                    )
                else:
                    found = f"{len(linter.files)} files"
                    errors = str(linter.number_errors)
                if (
                    config.exists("VALIDATE_ALL_CODEBASE")
                    and config.get("VALIDATE_ALL_CODEBASE") == "false"
                ):
                    message = f"This PR introduces {errors} lint problems to {found}."
                else:
                    message = f"This codebase containts {errors} lint problems in {found}."

                linter_url = f"{url}-{linter.linter_name}"
                self.submit_report(message, result, safe, linter.elapsed_time_s, linter_url, linter.linter_name)
            else:
                pass
        else:
            logging.debug(
                f"Skipped post of Bitbucket Status for {self.master.descriptor_id} with {self.master.linter_name}"
            )

    def submit_report(self, message, result, safe, duration, url, suffix=None):
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        if not suffix:
            title = "Mega-Linter scan report"
            reporter = "mega-linter"
        else:
            title = f"Mega-Linter {suffix} scan report"
            reporter = f"mega-linter-{suffix}"

        data = {
            "title": title,
            "details": message,
            "report_type": "BUG",
            "reporter": reporter,
            "result": result,
            "data": [
                {"title": "Duration (seconds)", "type": "DURATION", "value": duration},
                {"title": "Safe to merge?", "type": "BOOLEAN", "value": safe},
            ],
        }
        try:
            proxies = {"http": "host.docker.internal:29418"}
            import json
            response = requests.put(url, headers=headers, data=json.dumps(data), proxies=proxies)
            if 200 <= response.status_code < 299:
                logging.debug(
                    f"Successfully posted Bitbucket Status for {self.master.descriptor_id} "
                    f"with {self.master.linter_name}"
                )
            else:

                logging.warning(
                    f"[Bitbucket Status Reporter] Error posting Status for {self.master.descriptor_id}"
                    f"with {self.master.linter_name}: {response.status_code}\n"
                    f"Bitbucket API response: {response.text}"
                )
        except ConnectionError as e:
            logging.warning(
                f"[Bitbucket Status Reporter] Error putting Status for {self.master.descriptor_id}"
                f"with {self.master.linter_name}: Connection error {str(e)}"
            )
        except Exception as e:
            logging.warning(
                f"[Bitbucket Status Reporter] Error putting Status for {self.master.descriptor_id}"
                f"with {self.master.linter_name}: Error {str(e)}"
            )
