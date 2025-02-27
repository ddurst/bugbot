# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Any, Dict, List, Set

from libmozdata import utils as lmdutils
from libmozdata.bugzilla import Bugzilla

from bugbot import utils
from bugbot.bzcleaner import BzCleaner
from bugbot.history import History
from bugbot.webcompat_priority import WebcompatPriority

FIELD_NAME_TO_LABEL = {
    "keywords": "Keywords",
    "severity": "Severity",
    "whiteboard": "Whiteboard",
    "cf_accessibility_severity": "Accessibility Severity",
    "cf_performance_impact": "Performance Impact",
    "regressed_by": "Regressed by",
    "status": "Status",
    "cf_webcompat_priority": "Webcompat Priority",
}

FIELD_LABEL_TO_NAME = {label: name for name, label in FIELD_NAME_TO_LABEL.items()}


class DuplicateCopyMetadata(BzCleaner):
    def __init__(self, last_modification_days: int = 7):
        """Constructor
        Args:
            last_modification_days: Number of days to look back for bugs that
                were modified.
        """
        super().__init__()

        self.last_modification_date = lmdutils.get_date("today", last_modification_days)

    def description(self):
        return "Copied fields from duplicate bugs"

    def handle_bug(self, bug, data):
        if bug["last_change_time_non_bot"] < self.last_modification_date:
            return None

        data[str(bug["id"])] = bug

        return bug

    def get_bugs(self, date="today", bug_ids=[], chunk_size=None):
        dup_bugs = super().get_bugs(date, bug_ids, chunk_size)

        original_bug_ids = {bug["dupe_of"] for bug in dup_bugs.values()}
        original_bugs = {}

        def bughandler(bug, data):
            data: data[str(bug["id"])] = bug

        Bugzilla(
            original_bug_ids,
            include_fields=[
                "id",
                "summary",
                "keywords",
                "duplicates",
                "cf_accessibility_severity",
                "cf_performance_impact",
                "comments",
                "history",
                "status",
                "regressed_by",
                "is_open",
                "cf_webcompat_priority",
            ],
            bughandler=bughandler,
            bugdata=original_bugs,
        ).wait()

        results = {}
        for bug_id, bug in original_bugs.items():
            if not bug["is_open"]:
                continue

            copied_fields = {}
            for dup_bug_id in bug["duplicates"]:
                dup_bug_id = str(dup_bug_id)
                dup_bug = dup_bugs.get(dup_bug_id)
                if not dup_bug:
                    continue

                # TODO: Since the logic for copied fields is getting bigger,
                # consider refactoring it in a separate method.

                # Performance Impact: copy the assessment result from duplicates
                if bug.get("cf_performance_impact") == "---" and dup_bug.get(
                    "cf_performance_impact"
                ) not in ("---", "?", None):
                    if "cf_performance_impact" not in copied_fields:
                        copied_fields["cf_performance_impact"] = {
                            "from": [dup_bug["id"]],
                            "value": dup_bug["cf_performance_impact"],
                        }
                    else:
                        copied_fields["cf_performance_impact"]["from"].append(
                            dup_bug["id"]
                        )

                # Keywords: copy the `access` keyword from duplicates
                if "access" not in bug["keywords"] and "access" in dup_bug["keywords"]:
                    if "keywords" not in copied_fields:
                        copied_fields["keywords"] = {
                            "from": [dup_bug["id"]],
                            "value": "access",
                        }
                    else:
                        copied_fields["keywords"]["from"].append(dup_bug["id"])

                # Accessibility severity: copy the rating from duplicates
                if (
                    bug.get("cl_accessibility_severity") == "---"
                    and dup_bug.get("cl_accessibility_severity") != "---"
                ):
                    new_access_severity = dup_bug["cl_accessibility_severity"]
                    assert new_access_severity in ("s1", "s2", "s3", "s4")

                    if (
                        "cf_accessibility_severity" not in copied_fields
                        or new_access_severity
                        < copied_fields["cf_accessibility_severity"]["value"]
                    ):
                        copied_fields["cf_accessibility_severity"] = {
                            "from": [dup_bug["id"]],
                            "value": new_access_severity,
                        }
                    elif (
                        new_access_severity
                        == copied_fields["cf_accessibility_severity"]["value"]
                    ):
                        copied_fields["cf_accessibility_severity"]["from"].append(
                            dup_bug["id"]
                        )

                # Webcompat Priority: copy the `cf_webcompat_priority` from duplicates
                if (
                    bug.get("cf_webcompat_priority") == "---"
                    and dup_bug.get("cf_webcompat_priority")
                    in WebcompatPriority.NOT_EMPTY_VALUES
                ):
                    new_priority = dup_bug["cf_webcompat_priority"]

                    # Since the bug does not have a priority, it does not make
                    # sense to set it to `revisit`. Instead, we set it to `?` to
                    # request triage.
                    if new_priority == "revisit":
                        new_priority = "?"

                    if (
                        "cf_webcompat_priority" not in copied_fields
                        or WebcompatPriority(new_priority)
                        > WebcompatPriority(
                            copied_fields["cf_webcompat_priority"]["value"]
                        )
                    ):
                        copied_fields["cf_webcompat_priority"] = {
                            "from": [dup_bug["id"]],
                            "value": new_priority,
                        }
                    elif (
                        new_priority == copied_fields["cf_webcompat_priority"]["value"]
                    ):
                        copied_fields["cf_webcompat_priority"]["from"].append(
                            dup_bug["id"]
                        )

                # Status: confirm the bug if the duplicate was confirmed
                if bug["status"] == "UNCONFIRMED" and self.was_confirmed(dup_bug):
                    if "status" not in copied_fields:
                        copied_fields["status"] = {
                            "from": [dup_bug["id"]],
                            "value": "NEW",
                        }
                    else:
                        copied_fields["status"]["from"].append(dup_bug["id"])

                # Regressed by: move the regressed_by field to the duplicate of
                if dup_bug["regressed_by"]:
                    added_regressed_by = self.get_previously_added_regressors(bug)
                    new_regressed_by = {
                        regression_bug_id
                        for regression_bug_id in dup_bug["regressed_by"]
                        if regression_bug_id not in added_regressed_by
                        and regression_bug_id < int(bug_id)
                    }
                    if new_regressed_by:
                        if "regressed_by" not in copied_fields:
                            copied_fields["regressed_by"] = {
                                "from": [dup_bug["id"]],
                                "value": new_regressed_by,
                            }
                        else:
                            copied_fields["regressed_by"]["from"].append(dup_bug["id"])
                            copied_fields["regressed_by"]["value"] |= new_regressed_by

            previously_copied_fields = self.get_previously_copied_fields(bug)
            # We do not need to ignore the `regressed_by` field because we
            # already check the history to avoid overwriting the engineers.
            previously_copied_fields.discard("regressed_by")
            copied_fields = sorted(
                (
                    field,
                    change["value"],
                    change["from"],
                )
                for field, change in copied_fields.items()
                if field not in previously_copied_fields
            )

            if copied_fields:
                results[bug_id] = {
                    "id": bug_id,
                    "summary": bug["summary"],
                    "copied_fields": copied_fields,
                }

                self.set_autofix(bug, copied_fields)

        return results

    def set_autofix(self, bug: dict, copied_fields: List[tuple]) -> None:
        """Set the autofix for a bug

        Args:
            bug: The bug to set the autofix for.
            copied_fields: The list of copied fields with their values and the
                bugs they were copied from (field, value, source).
        """
        bug_id = str(bug["id"])
        autofix: Dict[str, Any] = {}

        duplicates = {id for _, _, source in copied_fields for id in source}

        # NOTE: modifying the following comment template should also be
        # reflected in the `get_previously_copied_fields` method.
        comment = (
            f"The following {utils.plural('field has', copied_fields, 'fields have')} been copied "
            f"from {utils.plural('a duplicate bug', duplicates, 'duplicate bugs')}:\n\n"
            "| Field | Value | Source |\n"
            "| ----- | ----- | ------ |\n"
        )

        for field, value, source in copied_fields:
            if field == "keywords":
                autofix["keywords"] = {"add": [value]}
            elif field == "cf_accessibility_severity":
                autofix["cf_accessibility_severity"] = value
            elif field == "cf_performance_impact":
                autofix["cf_performance_impact"] = value
            elif field == "cf_webcompat_priority":
                autofix["cf_webcompat_priority"] = value
            elif field == "status":
                autofix["status"] = value
            elif field == "regressed_by":
                autofix["regressed_by"] = {"add": list(value)}
                value = utils.english_list(sorted(f"bug {id}" for id in value))
            else:
                raise ValueError(f"Unsupported field: {field}")

            field_label = FIELD_NAME_TO_LABEL[field]
            source = utils.english_list(sorted(f"bug {id}" for id in source))
            comment += f"| {field_label} | {value} | {source} |\n"

        comment += "\n\n" + self.get_documentation()
        autofix["comment"] = {"body": comment}
        # The following is to reduce noise by having the bot to comme later to
        # add the `regression` keyword.
        if "regressed_by" in autofix and "regression" not in bug["keywords"]:
            if "keywords" not in autofix:
                autofix["keywords"] = {"add": ["regression"]}
            else:
                autofix["keywords"]["add"].append("regression")

        self.autofix_changes[bug_id] = autofix

    def get_previously_copied_fields(self, bug: dict) -> Set[str]:
        """Get the fields that have been copied from a bug's duplicates in the past.

        Args:
            bug: The bug to get the previously copied fields for.

        Returns:
            A set of previously copied fields.
        """
        previously_copied_fields = set()

        for comment in bug["comments"]:
            if comment["author"] != History.BOT or not comment["text"].startswith(
                "The following field"
            ):
                continue

            lines = comment["text"].splitlines()
            try:
                table_first_line = lines.index("| Field | Value | Source |")
            except ValueError:
                continue

            for line in lines[table_first_line + 2 :]:
                if not line.startswith("|"):
                    break
                field_label = line.split("|")[1].strip()
                field_name = FIELD_LABEL_TO_NAME[field_label]
                previously_copied_fields.add(field_name)

        return previously_copied_fields

    def get_previously_added_regressors(self, bug: dict) -> Set[int]:
        """Get the bug ids for regressors that have been added to a bug in the
        past.

        Args:
            bug: The bug to get the previously added regressors for.

        Returns:
            A set of ids for previously added regressors.
        """
        added_regressors = {
            int(bug_id)
            for entry in bug["history"]
            for change in entry["changes"]
            if change["field_name"] == "regressed_by"
            for bug_id in change["removed"].split(",")
            if bug_id
        }
        added_regressors.update(bug["regressed_by"])

        return added_regressors

    def was_confirmed(self, bug: dict) -> bool:
        """Check if the bug was confirmed."""

        for entry in reversed(bug["history"]):
            for change in entry["changes"]:
                if change["field_name"] != "status":
                    continue

                if change["removed"] in (
                    "REOPENED",
                    "CLOSED",
                    "RESOLVED",
                ):
                    break

                return change["removed"] != "UNCONFIRMED"

        return False

    def columns(self):
        return ["id", "summary", "copied_fields"]

    def get_bz_params(self, date):
        fields = [
            "history",
            "keywords",
            "cf_accessibility_severity",
            "cf_performance_impact",
            "dupe_of",
            "regressed_by",
            "cf_webcompat_priority",
            "last_change_time_non_bot",
        ]

        params = {
            "include_fields": fields,
            "resolution": "DUPLICATE",
            "chfieldfrom": self.last_modification_date,
            "chfield": [
                "resolution",
                "keywords",
                "status_whiteboard",
                "cf_accessibility_severity",
                "cf_performance_impact",
                "regressed_by",
                "cf_webcompat_priority",
            ],
        }

        return params


if __name__ == "__main__":
    DuplicateCopyMetadata().run()
