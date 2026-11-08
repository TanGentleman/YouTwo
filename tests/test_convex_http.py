import asyncio

import pytest

from youtwo.rag import backend
from youtwo.server.utils import async_convex_api_call


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


@pytest.fixture
def calls(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse({"sourceInfo": [{"filename": "notes.md"}]})

    monkeypatch.setenv("CONVEX_URL", "https://demo.convex.cloud")
    monkeypatch.setattr("requests.request", fake_request)
    return calls


def test_source_filenames_come_from_sources_info(calls):
    assert backend.get_source_filenames_from_convex() == ["notes.md"]
    assert calls[0][:2] == ("GET", "https://demo.convex.site/sources/info")


def test_requests_send_the_bearer_token(calls, monkeypatch):
    monkeypatch.setenv("YOUTWO_API_TOKEN", "secret")
    backend.get_source_filenames_from_convex()
    asyncio.run(async_convex_api_call("graph", "GET"))
    assert [c[2]["headers"]["Authorization"] for c in calls] == ["Bearer secret"] * 2
    assert calls[1][1] == "https://demo.convex.site/graph"


def test_no_token_sends_no_authorization_header(calls, monkeypatch):
    monkeypatch.delenv("YOUTWO_API_TOKEN", raising=False)
    asyncio.run(async_convex_api_call("graph", "GET"))
    assert "Authorization" not in calls[0][2]["headers"]
