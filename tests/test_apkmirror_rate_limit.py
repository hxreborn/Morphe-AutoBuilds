#!/usr/bin/env python3
"""Run directly: python tests/test_apkmirror_rate_limit.py"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.CRITICAL)

from src import apkmirror


class FakeResponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = ""


def test_retry_after_parsing():
    parse = apkmirror._retry_after_seconds
    assert parse(FakeResponse(429)) is None
    assert parse(FakeResponse(429, {"Retry-After": "7"})) == 7
    assert parse(FakeResponse(429, {"Retry-After": " 3 "})) == 3
    assert parse(FakeResponse(429, {"Retry-After": "0"})) == 1
    assert parse(FakeResponse(429, {"Retry-After": "-5"})) == 1
    assert parse(FakeResponse(429, {"Retry-After": "99999"})) == apkmirror._RATE_LIMIT_MAX_DELAY
    assert parse(FakeResponse(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})) is None


def test_cf_get_retries_429_then_succeeds(stub_session):
    calls = stub_session(lambda n: FakeResponse(429 if n < 3 else 200))
    assert apkmirror._cf_get("u").status_code == 200
    assert len(calls) == 3


def test_cf_get_gives_up_after_cap(stub_session):
    calls = stub_session(lambda n: FakeResponse(429))
    assert apkmirror._cf_get("u").status_code == 429
    assert len(calls) == apkmirror._RATE_LIMIT_RETRIES + 1


def test_cf_get_does_not_retry_success(stub_session):
    calls = stub_session(lambda n: FakeResponse(200))
    assert apkmirror._cf_get("u").status_code == 200
    assert len(calls) == 1


VARIANT_PAGE = """
<html><body>
<div class="table-row headerFont">
  <div class="table-cell">2.0</div><div class="table-cell">BUNDLE 27 S  157</div>
  <div class="table-cell">arm64-v8a</div><div class="table-cell">480-640dpi</div>
  <a class="accent_color" href="/variant-157/">go</a>
</div>
<div class="table-row headerFont">
  <div class="table-cell">2.0</div><div class="table-cell">BUNDLE 27 S  158</div>
  <div class="table-cell">arm64-v8a</div><div class="table-cell">480-640dpi</div>
  <a class="accent_color" href="/variant-158/">go</a>
</div>
<a class="downloadButton" href="/final/">dl</a>
<a id="download-link" href="/blob.apk">blob</a>
</body></html>
"""


class FakePage:
    status_code = 200
    headers: dict = {}
    text = VARIANT_PAGE
    content = VARIANT_PAGE.encode()
    url = "https://www.apkmirror.com/stub"

    def raise_for_status(self):
        pass


def test_version_code_selects_the_targeted_build():
    config = {
        "org": "paget96",
        "name": "internet-speed-speed-test-2",
        "type": "BUNDLE",
        "arch": "arm64-v8a",
        "dpi": "480-640",
        "package": "com.paget96.netspeedindicator",
    }
    pages = []
    apkmirror._cf_get = lambda url, **kwargs: (pages.append(url), FakePage())[1]

    def visited(fragment):
        return any(fragment in url for url in pages)

    assert apkmirror.get_download_link("2.0", "network-guru", dict(config), "arm64-v8a")
    assert visited("/variant-157/")

    pages.clear()
    pinned = dict(config, version_code=158)
    assert apkmirror.get_download_link("2.0", "network-guru", pinned, "arm64-v8a")
    assert visited("/variant-158/")
    assert not visited("/variant-157/")


def main():
    real_get, real_sleep = apkmirror.session.get, apkmirror.time.sleep
    real_cf_get = apkmirror._cf_get
    apkmirror.time.sleep = lambda _: None

    def stub_session(responder):
        calls = []
        def fake_get(url, **kwargs):
            calls.append(url)
            return responder(len(calls))
        apkmirror.session.get = fake_get
        return calls

    try:
        test_retry_after_parsing()
        test_cf_get_retries_429_then_succeeds(stub_session)
        test_cf_get_gives_up_after_cap(stub_session)
        test_cf_get_does_not_retry_success(stub_session)
        test_version_code_selects_the_targeted_build()
    finally:
        apkmirror.session.get, apkmirror.time.sleep = real_get, real_sleep
        apkmirror._cf_get = real_cf_get

    print("ok")


if __name__ == "__main__":
    main()
