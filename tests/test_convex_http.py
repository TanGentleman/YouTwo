import pytest

from youtwo.rag import backend


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
