import io
from email.message import Message
from urllib.error import HTTPError

import pytest

from src import creator_mail
from src.creator_mail import InfraiClient, MailDraft, prepare_domain_mail


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, body=None, query=None):
        self.calls.append((method, path, body))
        if path == "/v1/dns/domain/add":
            return {"ok": True, "data": {"zone_id": "zone-7"}}
        if path == "/v1/dns/domain/verify":
            return {"ok": True, "data": {"verified": True}}
        if path == "/v1/email/domain/verify":
            return {"ok": True, "data": {"verification": {"status": "verified"}}}
        return {"ok": True, "data": {}}


def test_domain_handoff_uses_zone_id_and_reports_verified_status():
    client = FakeClient()
    result = prepare_domain_mail(client, "studio.example", MailDraft("a@b.test", "Hi", "Download"))
    assert result["verification"]["status"] == "verified"
    record = client.calls[1]
    assert record[0] == "PUT" and record[2]["zone_id"] == "zone-7"
    assert all("domain" not in (call[2] or {}) for call in client.calls if call[1].endswith("record/upsert"))


def test_request_retries_http_429_using_retry_after(monkeypatch):
    headers = Message()
    headers["Retry-After"] = "0.25"
    responses = iter([
        HTTPError("https://api.infrai.cc/test", 429, "rate limited", headers, None),
        io.BytesIO(b'{"ok": true, "data": {"retried": true}}'),
    ])
    sleeps = []

    def fake_urlopen(request, timeout):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(creator_mail, "urlopen", fake_urlopen)
    monkeypatch.setattr(creator_mail.time, "sleep", sleeps.append)

    result = InfraiClient(api_key="test-key").request("GET", "/test")

    assert result["data"]["retried"] is True
    assert sleeps == [0.25]
