import io
import json
import sys

import pytest

from bump2v import output
from bump2v.output import EXIT_DIRTY, Failure, Output


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


def _tty_stderr(monkeypatch):
    # Install inside the test body: pytest re-installs its own sys.stderr capture
    # between fixture setup and the test call.
    stream = FakeTTY()
    monkeypatch.setattr(sys, "stderr", stream)
    for name in ("NO_COLOR", "CI", "CLAUDECODE"):
        monkeypatch.delenv(name, raising=False)
    return stream


class TestFancy:
    def test_emoji_on_an_interactive_terminal(self, monkeypatch):
        stream = _tty_stderr(monkeypatch)
        Output().say("plain", "fancy 🚀")
        assert stream.getvalue() == "fancy 🚀\n"

    @pytest.mark.parametrize("name", ["NO_COLOR", "CI", "CLAUDECODE"])
    def test_plain_when_an_opt_out_variable_is_set(self, monkeypatch, name):
        stream = _tty_stderr(monkeypatch)
        monkeypatch.setenv(name, "1")
        Output().say("plain", "fancy 🚀")
        assert stream.getvalue() == "plain\n"

    def test_plain_when_not_a_terminal(self, monkeypatch):
        stream = io.StringIO()
        monkeypatch.setattr(sys, "stderr", stream)
        Output().say("plain", "fancy 🚀")
        assert stream.getvalue() == "plain\n"


class TestJson:
    def test_data_is_suppressed_and_result_printed(self, capsys):
        out = Output(json_mode=True)
        out.data("human line")
        out.result("plan", {"new_version": "1.0.1"})
        printed = json.loads(capsys.readouterr().out)
        assert printed == {"format_version": "1.0", "command": "plan", "ok": True, "new_version": "1.0.1"}

    def test_failure_shape(self, capsys):
        Output(json_mode=True).failure(
            "check", Failure(EXIT_DIRTY, "dirty_tree", "not clean", hint="commit", details={"files": []})
        )
        printed = json.loads(capsys.readouterr().out)
        assert printed["ok"] is False and printed["exit_code"] == 3
        assert printed["error"] == {"code": "dirty_tree", "message": "not clean", "hint": "commit", "retryable": False}
        assert printed["files"] == []


def test_print_survives_a_stream_that_cannot_encode():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    output._print("1.0.0 → 1.0.1 🚀", stream)
    stream.flush()
    assert stream.buffer.getvalue() == b"1.0.0 ? 1.0.1 ?\r\n" or stream.buffer.getvalue() == b"1.0.0 ? 1.0.1 ?\n"
