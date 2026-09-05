"""Tests for the GitLab work: reading an issue, proposing a fix, merging.

The transport is injected, so nothing here touches gitlab.com. What matters is
the shape of the work: a fix lands on its own branch behind a merge request,
and merging is a separate step nobody takes by accident.
"""

import unittest

from assistant.gitlab_agent import (
    GitLabClient,
    GitLabError,
    gitlab_find_file,
    gitlab_list_issues,
    gitlab_merge,
    gitlab_propose_fix,
    gitlab_read_file,
    gitlab_read_issue,
)


class FakeGitLab:
    """Answers like GitLab does, and records what it was asked to do."""

    def __init__(self, responses=None, fail=None):
        self.calls = []
        self.fail = fail or set()
        self.responses = responses or {}

    def __call__(self, method, url, payload=None):
        self.calls.append({"method": method, "url": url, "payload": payload})

        for marker in self.fail:
            if marker in url:
                raise GitLabError(f"GitLab said no: 403 on {marker}")

        path = url.split("?")[0]

        # An exact ending wins, so "/raw" does not lose to the project URL it
        # is built on top of; otherwise fall back to the longest match.
        for marker in sorted(self.responses, key=len, reverse=True):
            if path.endswith(marker):
                return self.responses[marker]
        for marker in sorted(self.responses, key=len, reverse=True):
            if marker in url:
                return self.responses[marker]
        return {}


def client(**kwargs):
    fake = FakeGitLab(**kwargs)
    return GitLabClient(transport=fake), fake


class ReadingTests(unittest.TestCase):
    def test_issues_are_listed_with_their_numbers(self):
        api, _ = client(responses={"/issues": [
            {"iid": 7, "title": "Login button does nothing", "labels": ["bug"]},
            {"iid": 9, "title": "Typo in the README", "labels": []},
        ]})

        result = gitlab_list_issues("team/app", _client_override=api)

        self.assertIn("#7 Login button does nothing", result)
        self.assertIn("[bug]", result)
        self.assertIn("#9 Typo in the README", result)

    def test_a_project_path_is_encoded_for_the_api(self):
        api, fake = client(responses={"/issues": []})

        gitlab_list_issues("team/sub/app", _client_override=api)

        self.assertIn("projects/team%2Fsub%2Fapp/issues", fake.calls[0]["url"])

    def test_no_issues_is_said_plainly(self):
        api, _ = client(responses={"/issues": []})

        self.assertIn("No opened issues", gitlab_list_issues("team/app",
                                                             _client_override=api))

    def test_an_issue_is_read_with_its_comments(self):
        api, _ = client(responses={
            "/issues/7/notes": [
                {"body": "Happens on Firefox too", "author": {"name": "Ana"},
                 "system": False},
                {"body": "changed the milestone", "author": {"name": "bot"},
                 "system": True},
            ],
            "/issues/7": {"iid": 7, "title": "Login button does nothing",
                          "state": "opened", "labels": ["bug"],
                          "description": "Clicking Login does nothing on Safari."},
        })

        result = gitlab_read_issue("team/app", 7, _client_override=api)

        self.assertIn("Issue #7: Login button does nothing", result)
        self.assertIn("Clicking Login does nothing on Safari.", result)
        self.assertIn("Ana: Happens on Firefox too", result)

    def test_system_notes_are_left_out_of_the_comments(self):
        api, _ = client(responses={
            "/issues/7/notes": [{"body": "changed the milestone",
                                 "author": {"name": "bot"}, "system": True}],
            "/issues/7": {"iid": 7, "title": "x", "description": ""},
        })

        self.assertIn("Comments:\nnone",
                      gitlab_read_issue("team/app", 7, _client_override=api))

    def test_searching_finds_the_file_an_issue_is_about(self):
        api, _ = client(responses={"/search": [
            {"path": "app/login.py", "startline": 42},
            {"path": "app/login.py", "startline": 51},
        ]})

        result = gitlab_find_file("team/app", "login", _client_override=api)

        self.assertIn("app/login.py", result)

    def test_a_file_is_read_from_the_default_branch(self):
        api, fake = client(responses={
            "projects/team%2Fapp": {"default_branch": "trunk"},
            "/raw": "def login():\n    pass\n",
        })

        result = gitlab_read_file("team/app", "app/login.py", _client_override=api)

        self.assertIn("app/login.py on trunk", result)
        self.assertIn("def login()", result)

    def test_a_long_file_is_trimmed_rather_than_flooding_the_model(self):
        api, _ = client(responses={"projects/team%2Fapp": {"default_branch": "main"},
                                   "/raw": "x" * 9000})

        result = gitlab_read_file("team/app", "big.py", _client_override=api)

        self.assertIn("[file trimmed]", result)

    def test_a_refusal_is_reported_rather_than_raised(self):
        api, _ = client(fail={"/issues"})

        self.assertIn("GitLab said no",
                      gitlab_list_issues("team/app", _client_override=api))


class ProposingTests(unittest.TestCase):
    def setUp(self):
        self.api, self.fake = client(responses={
            "projects/team%2Fapp": {"default_branch": "main"},
            "/merge_requests": {"iid": 12, "web_url": "https://gitlab.com/mr/12"},
        })

    def test_a_fix_goes_onto_its_own_branch(self):
        gitlab_propose_fix("team/app", 7, "app/login.py", "fixed code",
                           summary="handle the Safari case", _client_override=self.api)

        branch_call = next(call for call in self.fake.calls
                           if call["url"].endswith("/repository/branches"))
        self.assertEqual("vave/issue-7", branch_call["payload"]["branch"])
        self.assertEqual("main", branch_call["payload"]["ref"])

    def test_the_commit_carries_the_whole_new_file(self):
        gitlab_propose_fix("team/app", 7, "app/login.py", "fixed code",
                           _client_override=self.api)

        commit = next(call for call in self.fake.calls
                      if call["url"].endswith("/repository/commits"))
        self.assertEqual("vave/issue-7", commit["payload"]["branch"])
        self.assertEqual([{"action": "update", "file_path": "app/login.py",
                           "content": "fixed code"}], commit["payload"]["actions"])

    def test_the_merge_request_closes_the_issue_and_names_the_change(self):
        gitlab_propose_fix("team/app", 7, "app/login.py", "fixed code",
                           summary="handle the Safari case", _client_override=self.api)

        request = next(call for call in self.fake.calls
                       if call["url"].endswith("/merge_requests"))
        self.assertEqual("vave/issue-7", request["payload"]["source_branch"])
        self.assertEqual("main", request["payload"]["target_branch"])
        self.assertIn("handle the Safari case", request["payload"]["title"])
        self.assertIn("Closes #7", request["payload"]["description"])

    def test_proposing_never_merges(self):
        result = gitlab_propose_fix("team/app", 7, "app/login.py", "fixed code",
                                    _client_override=self.api)

        self.assertEqual([], [call for call in self.fake.calls
                              if call["url"].endswith("/merge")])
        self.assertIn("It is not merged", result)

    def test_an_existing_branch_is_committed_onto_rather_than_failing(self):
        api, fake = client(responses={
            "projects/team%2Fapp": {"default_branch": "main"},
            "/merge_requests": {"iid": 12},
        }, fail={"/repository/branches"})

        result = gitlab_propose_fix("team/app", 7, "app/login.py", "code",
                                    _client_override=api)

        self.assertIn("Opened merge request !12", result)


class MergingTests(unittest.TestCase):
    def test_merging_is_its_own_step(self):
        api, fake = client(responses={"/merge": {"target_branch": "main",
                                                 "web_url": "https://gitlab.com/mr/12"}})

        result = gitlab_merge("team/app", 12, _client_override=api)

        self.assertIn("Merged !12 into main", result)
        self.assertEqual("PUT", fake.calls[0]["method"])

    def test_a_refused_merge_is_reported(self):
        api, _ = client(fail={"/merge"})

        self.assertIn("GitLab said no", gitlab_merge("team/app", 12,
                                                     _client_override=api))


class CapabilityTests(unittest.TestCase):
    def test_each_tool_asks_for_the_right_level_of_access(self):
        from assistant.control.capabilities import capability_for_tool, risk_for

        self.assertEqual("gitlab.read", capability_for_tool("gitlab_read_issue"))
        self.assertEqual("gitlab.write", capability_for_tool("gitlab_propose_fix"))
        self.assertEqual("gitlab.merge", capability_for_tool("gitlab_merge"))
        self.assertEqual("critical", risk_for("gitlab.merge").value)
        self.assertEqual("high", risk_for("browser.interact").value)
        self.assertEqual("low", risk_for("browser.navigate").value)


if __name__ == "__main__":
    unittest.main()
