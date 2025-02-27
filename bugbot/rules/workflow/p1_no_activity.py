# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from bugbot import utils
from bugbot.bzcleaner import BzCleaner
from bugbot.escalation import Escalation, NoActivityDays
from bugbot.nag_me import Nag


class P1NoActivity(BzCleaner, Nag):
    def __init__(self):
        super(P1NoActivity, self).__init__()
        self.escalation = Escalation(
            self.people,
            data=utils.get_config(self.name(), "escalation"),
            skiplist=utils.get_config("workflow", "supervisor_skiplist", []),
        )

    def description(self):
        return "P1 bugs and no activity for {} days".format(self.ndays)

    def nag_template(self):
        return self.template()

    def get_extra_for_template(self):
        return {"ndays": self.ndays}

    def get_extra_for_nag_template(self):
        return self.get_extra_for_template()

    def ignore_meta(self):
        return True

    def has_last_comment_time(self):
        return True

    def has_assignee(self):
        return True

    def has_product_component(self):
        return True

    def columns(self):
        return ["component", "id", "summary", "last_comment", "assignee"]

    def set_people_to_nag(self, bug, buginfo):
        priority = "high"
        if not self.filter_bug(priority):
            return None

        # check if the product::component is in the list
        if not utils.check_product_component(self.components, bug):
            return None

        owner = bug["triage_owner"]
        assignee = bug["assigned_to"]
        if not self.add(assignee, buginfo, priority=priority, triage_owner=owner):
            self.add_no_manager(buginfo["id"])

        return bug

    def get_bz_params(self, date):
        self.ndays = NoActivityDays(self.name()).get(
            (utils.get_next_release_date() - self.nag_date).days
        )
        fields = ["triage_owner", "assigned_to"]
        self.components = utils.get_config("workflow", "components")
        params = {
            "component": utils.get_components(self.components),
            "bug_type": "defect",
            "include_fields": fields,
            "resolution": "---",
            "f1": "priority",
            "o1": "equals",
            "v1": "P1",
            "f2": "days_elapsed",
            "o2": "greaterthaneq",
            "v2": self.ndays,
        }

        utils.get_empty_assignees(params)

        return params


if __name__ == "__main__":
    P1NoActivity().run()
