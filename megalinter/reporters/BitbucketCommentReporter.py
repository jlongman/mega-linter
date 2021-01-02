#!/usr/bin/env python3
"""
Bitbucket Status reporter
Post a Bitbucket status for each linter
"""
import logging
import os

# import bitbucket
from megalinter import Reporter, config
from pytablewriter import MarkdownTableWriter

BRANCH = "master"
URL_ROOT = "https://bitbucket.com/nvuillam/mega-linter/tree/" + BRANCH
DOCS_URL_ROOT = URL_ROOT + "/docs"
DOCS_URL_DESCRIPTORS_ROOT = DOCS_URL_ROOT + "/descriptors"


def log_link(label, url):
    if url == "":
        return label
    else:
        return f"[{label}]({url})"


class BitbucketCommentReporter(Reporter):
    name = "BITBUCKET_COMMENT"
    scope = "mega-linter"

    bitbucket_api_url = "https://api.bitbucket.org"
    bitbucket_server_url = "https://bitbucket.org"
    gh_url = "https://nvuillam.bitbucket.io/mega-linter"

    def __init__(self, params=None):
        # Activate Bitbucket Comment by default
        self.is_active = True
        super().__init__(params)

    def manage_activation(self):
        # Disable status for each linter if MULTI_STATUS is 'false'
        if config.exists("MULTI_STATUS") and config.get("MULTI_STATUS") == "false":
            self.is_active = False
        if not config.exists("BITBUCKET_CLONE_DIR"):
            self.is_active = False

        # FIXME evaluate these in context
        if config.get("BITBUCKET_COMMENT_REPORTER", "true") != "true":
            self.is_active = False
        elif config.get("POST_BITBUCKET_COMMENT", "true") == "true":  # Legacy - true by default
            self.is_active = True

        self.is_active = False  # FIXME this reporter hasn't been started yet


    def produce_report(self):
        # Post comment on Bitbucket pull request
        if config.get("BITBUCKET_CLONE_DIR", "") != "":
            bitbucket_repo = config.get("BITBUCKET_REPOSITORY")
            bitbucket_server_url = config.get(
                "BITBUCKET_SERVER_URL", self.bitbucket_server_url
            )
            bitbucket_api_url = config.get("BITBUCKET_API_URL", self.bitbucket_api_url)
            run_id = config.get("BITBUCKET_RUN_ID")
            sha = config.get("BITBUCKET_SHA")
            if run_id is not None:
                action_run_url = (
                    f"{bitbucket_server_url}/{bitbucket_repo}/actions/runs/{run_id}"
                )
            else:
                action_run_url = ""
            table_header = ["Descriptor", "Linter", "Found", "Fixed", "Errors"]
            if self.master.show_elapsed_time is True:
                table_header += ["Elapsed time"]
            table_data_raw = [table_header]
            for linter in self.master.linters:
                if linter.is_active is True:
                    status = (
                        "✅"
                        if linter.status == "success" and linter.return_code == 0
                        else ":orange_circle:"
                        if linter.status != "success" and linter.return_code == 0
                        else "❌"
                    )
                    first_col = f"{status} {linter.descriptor_id}"
                    lang_lower = linter.descriptor_id.lower()
                    linter_name_lower = linter.linter_name.lower().replace("-", "_")
                    linter_doc_url = f"{DOCS_URL_DESCRIPTORS_ROOT}/{lang_lower}_{linter_name_lower}.md"
                    linter_link = f"[{linter.linter_name}]({linter_doc_url})"
                    nb_fixed_cell = (
                        str(linter.number_fixed) if linter.try_fix is True else ""
                    )
                    if linter.cli_lint_mode == "project":
                        found = "yes"
                        nb_fixed_cell = "yes" if nb_fixed_cell != "" else nb_fixed_cell
                        errors_cell = (
                            log_link("**yes**", action_run_url)
                            if linter.number_errors > 0
                            else "no"
                        )
                    else:
                        found = str(len(linter.files))
                        errors_cell = (
                            log_link(f"**{linter.number_errors}**", action_run_url)
                            if linter.number_errors > 0
                            else linter.number_errors
                        )
                    table_line = [
                        first_col,
                        linter_link,
                        found,
                        nb_fixed_cell,
                        errors_cell,
                    ]
                    if self.master.show_elapsed_time is True:
                        table_line += [str(round(linter.elapsed_time_s, 2)) + "s"]
                    table_data_raw += [table_line]
            # Build markdown table
            table_data_raw.pop(0)
            writer = MarkdownTableWriter(
                headers=table_header, value_matrix=table_data_raw
            )
            table_content = str(writer) + os.linesep if len(table_data_raw) > 1 else ""
            status = "✅" if self.master.return_code == 0 else "❌"
            status_with_href = (
                status
                + " "
                + log_link(f"**{self.master.status.upper()}**", action_run_url)
            )
            p_r_msg = (
                f"## [Mega-Linter]({self.gh_url}) status: {status_with_href}"
                + os.linesep
                + os.linesep
            )
            p_r_msg += table_content + os.linesep
            if action_run_url != "":
                p_r_msg += (
                    "See errors details in [**artifact Mega-Linter reports** on "
                    f"Bitbucket Action page]({action_run_url})" + os.linesep
                )
            else:
                p_r_msg += "See errors details in Mega-Linter reports" + os.linesep
            if self.master.validate_all_code_base is False:
                p_r_msg += (
                    "_Set `VALIDATE_ALL_CODEBASE: true` in mega-linter.yml to validate "
                    + "all sources, not only the diff_"
                    + os.linesep
                )
            if self.master.flavor_suggestions is not None:
                p_r_msg += (
                    os.linesep
                    + "You could have the same capabilities but better runtime performances"
                    " if you use a Mega-Linter flavor:" + os.linesep
                )
                for suggestion in self.master.flavor_suggestions:
                    build_version = os.environ.get("BUILD_VERSION", "v4")
                    action_version = (
                        "v4"
                        if "v4" in build_version or len(build_version) > 20
                        else "insiders"
                        if build_version == "latest"
                        else build_version
                    )
                    action_path = f"nvuillam/mega-linter/flavors/{suggestion['flavor']}@{action_version}"
                    p_r_msg += (
                        f"- [**{action_path}**]({self.gh_url}/flavors/{suggestion['flavor']}/)"
                        f" ({suggestion['linters_number']} linters)"
                    )
            logging.debug("\n" + p_r_msg)
            # Post comment on pull request if found
            bitbucket_auth = (
                config.get("PAT")
                if config.get("PAT", "") != ""
                else config.get("BITBUCKET_TOKEN")
            )
            raise Exception("not implemented")

            # g = bitbucket.Bitbucket(
            #     base_url=bitbucket_api_url, login_or_token=bitbucket_auth
            # )
            repo = g.get_repo(bitbucket_repo)
            commit = repo.get_commit(sha=sha)
            pr_list = commit.get_pulls()
            if pr_list.totalCount == 0:
                logging.info(
                    "[Bitbucket Comment Reporter] No pull request was found, so no comment has been posted"
                )
                return
            for pr in pr_list:
                # Ignore if PR is already merged
                if pr.is_merged():
                    continue
                # Check if there is already a comment from Mega-Linter
                existing_comment = None
                existing_comments = pr.get_issue_comments()
                for comment in existing_comments:
                    if (
                        "See errors details in [**artifact Mega-Linter reports** on"
                        in comment.body
                    ):
                        existing_comment = comment
                # Process comment
                try:
                    # Edit if there is already a Mega-Linter comment
                    if existing_comment is not None:
                        existing_comment.edit(p_r_msg)
                    # Or create a new PR comment
                    else:
                        pr.create_issue_comment(p_r_msg)
                    logging.debug(f"Posted Bitbucket comment: {p_r_msg}")
                    logging.info(
                        f"[Bitbucket Comment Reporter] Posted summary as comment on {bitbucket_repo} #PR{pr.number}"
                    )
                except bitbucket.BitbucketException as e:
                    logging.warning(
                        f"[Bitbucket Comment Reporter] Unable to post pull request comment: {str(e)}.\n"
                        "To enable this function, please :\n"
                        "1. Create a Personal Access Token (https://docs.bitbucket.org/en/free-pro-team@"
                        "latest/bitbucket/authenticating-to-bitbucket/creating-a-personal-access-token)\n"
                        "2. Create a secret named PAT with its value on your repository (https://docs."
                        "bitbucket.org/en/free-pro-team@latest/actions/reference/encrypted-secrets#"
                        "creating-encrypted-secrets-for-a-repository)"
                        "3. Define PAT={{secrets.PAT}} in your Bitbucket action environment variables"
                    )
                except Exception as e:
                    logging.warning(
                        f"[Bitbucket Comment Reporter] Error while posting comment: \n{str(e)}"
                    )
        # Not in bitbucket context, or env var POST_BITBUCKET_COMMENT = false
        else:
            logging.info(
                "[Bitbucket Comment Reporter] No Bitbucket Token found, so skipped post of PR comment"
            )