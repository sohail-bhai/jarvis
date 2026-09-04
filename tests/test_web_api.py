"""Tests for calling any service's API.

The point of this tool is that a new service needs no new code - only a stored
credential and a URL. These check that, and that the credential never travels
through the model.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from assistant.control.service import ControlPlane
from assistant.control.store import ControlStore
from assistant.web_api import WebApiError, call, web_api_call, web_api_get


class FakeService:
    """Records the call and answers like a JSON API."""

    def __init__(self, status=200, payload=None, fail=None):
        self.calls = []
        self.status = status
        self.payload = payload if payload is not None else {"ok": True}
        self.fail = fail

    def __call__(self, method, url, body, headers):
        self.calls.append({"method": method, "url": url, "body": body,
                           "headers": headers})
        if self.fail:
            raise WebApiError(self.fail)
        return self.status, self.payload


class RequestTests(unittest.TestCase):
    def test_a_read_returns_the_body_and_the_status(self):
        service = FakeService(payload=[{"number": 12, "title": "Broken login"}])

        result = web_api_get("https://api.github.com/repos/x/y/issues",
                             _transport=service)

        self.assertIn("HTTP 200", result)
        self.assertIn("Broken login", result)

    def test_query_parameters_are_added_to_the_url(self):
        service = FakeService()

        web_api_get("https://api.example.com/items", params={"state": "open"},
                    _transport=service)

        self.assertIn("items?state=open", service.calls[0]["url"])

    def test_parameters_join_an_address_that_already_has_some(self):
        service = FakeService()

        web_api_get("https://api.example.com/items?page=2", params={"state": "open"},
                    _transport=service)

        self.assertIn("?page=2&state=open", service.calls[0]["url"])

    def test_a_write_sends_the_body(self):
        service = FakeService(status=201)

        web_api_call("POST", "https://api.example.com/issues",
                     body={"title": "Something is broken"}, _transport=service)

        self.assertEqual("POST", service.calls[0]["method"])
        self.assertEqual({"title": "Something is broken"}, service.calls[0]["body"])

    def test_a_body_sent_as_a_string_is_still_understood(self):
        service = FakeService()

        web_api_call("POST", "https://api.example.com/issues",
                     body='{"title": "from a string"}', _transport=service)

        self.assertEqual({"title": "from a string"}, service.calls[0]["body"])

    def test_a_safe_method_is_treated_as_a_read(self):
        service = FakeService()

        web_api_call("GET", "https://api.example.com/items", _transport=service)

        self.assertEqual("GET", service.calls[0]["method"])

    def test_an_address_without_a_scheme_is_refused(self):
        self.assertIn("must start with http",
                      web_api_get("api.example.com/items", _transport=FakeService()))

    def test_a_refusal_from_the_service_is_reported_not_raised(self):
        service = FakeService(fail="403 from https://api.example.com: forbidden")

        result = web_api_get("https://api.example.com/items", _transport=service)

        self.assertIn("403", result)

    def test_a_long_response_is_trimmed(self):
        service = FakeService(payload={"items": ["x" * 100 for _ in range(200)]})

        self.assertIn("[trimmed]", web_api_get("https://api.example.com/items",
                                               _transport=service))


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix="jarvis-webapi-test-")
        self.store = ControlStore(Path(self.tempdir) / "control.db")
        self.plane = ControlPlane(store=self.store)
        self.plane.secrets.put("github_token", "ghp_realtoken")

        import assistant.control.service as service
        self._previous = service._control_plane
        service._control_plane = self.plane

    def tearDown(self):
        import assistant.control.service as service
        service._control_plane = self._previous
        self.store.close()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_a_named_credential_is_resolved_into_the_header(self):
        service = FakeService()

        web_api_get("https://api.github.com/user", auth_secret="github_token",
                    _transport=service)

        self.assertEqual("Bearer ghp_realtoken",
                         service.calls[0]["headers"]["Authorization"])

    def test_the_secret_reference_form_is_accepted_too(self):
        service = FakeService()

        web_api_get("https://api.github.com/user",
                    auth_secret="secret://github_token", _transport=service)

        self.assertIn("ghp_realtoken", service.calls[0]["headers"]["Authorization"])

    def test_each_service_gets_the_header_it_expects(self):
        service = FakeService()

        web_api_get("https://gitlab.com/api/v4/projects",
                    auth_secret="github_token", auth_style="private-token",
                    _transport=service)

        self.assertEqual("ghp_realtoken", service.calls[0]["headers"]["PRIVATE-TOKEN"])

    def test_a_missing_credential_says_which_one_to_store(self):
        result = web_api_get("https://api.example.com/x", auth_secret="jira_token",
                             _transport=FakeService())

        self.assertIn("no stored credential called 'jira_token'", result)

    def test_an_unknown_auth_style_is_refused_clearly(self):
        result = web_api_get("https://api.example.com/x", auth_secret="github_token",
                             auth_style="magic", _transport=FakeService())

        self.assertIn("not a way of sending a credential", result)

    def test_no_credential_means_no_authorization_header(self):
        service = FakeService()

        web_api_get("https://api.example.com/public", _transport=service)

        self.assertNotIn("Authorization", service.calls[0]["headers"])


class CapabilityTests(unittest.TestCase):
    def test_reading_and_changing_carry_different_risk(self):
        from assistant.control.capabilities import capability_for_tool, risk_for

        self.assertEqual("medium", risk_for(capability_for_tool("web_api_get")).value)
        self.assertEqual("high", risk_for(capability_for_tool("web_api_call")).value)


if __name__ == "__main__":
    unittest.main()
