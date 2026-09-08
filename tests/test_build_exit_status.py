"""An app no store serves is a skip; a patch failure is still a failure."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import __main__ as builder


def _run(result):
    os.environ.update(APP_NAME="splitwise", SOURCE="rushiranpise", ARCH="arm64-v8a")
    original = builder.run_build
    builder.run_build = lambda *args: result
    try:
        builder.main()
    finally:
        builder.run_build = original


def test():
    _run(builder.UNAVAILABLE)

    try:
        _run(None)
    except SystemExit as e:
        assert e.code == 1, e.code
    else:
        raise AssertionError("a patch failure must still exit 1")

    print("ok")


if __name__ == "__main__":
    test()
