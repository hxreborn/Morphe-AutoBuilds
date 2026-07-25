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


def main():
    real_get, real_sleep = apkmirror.session.get, apkmirror.time.sleep
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
    finally:
        apkmirror.session.get, apkmirror.time.sleep = real_get, real_sleep

    print("ok")


if __name__ == "__main__":
    main()
