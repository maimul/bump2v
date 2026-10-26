"""How bump2v talks: messages to stderr, data to stdout, exit codes, and --json.

Human output keeps the emoji only on an interactive terminal. In CI, in a pipe, or
when NO_COLOR or CLAUDECODE is set, messages are plain text.
"""
import json
import os
import sys

# Exit codes. Documented in the README; scripts and agents branch on them.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_DIRTY = 3
EXIT_VERSION_NOT_FOUND = 4
EXIT_TAG_EXISTS = 5
EXIT_PUSH_FAILED = 6
EXIT_NOTHING_TO_RELEASE = 7

# Bump this when the --json shape changes: minor for added fields, major for
# removed or renamed ones.
FORMAT_VERSION = "1.0"


class Failure(Exception):
    """An expected failure, with a stable code and a hint for what to do next."""

    def __init__(self, exit_code, code, message, hint=None, retryable=False, details=None):
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code
        self.message = message
        self.hint = hint
        self.retryable = retryable
        # Extra result fields for --json (e.g. the per-file results of a failed check).
        self.details = details or {}

    def as_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "retryable": self.retryable,
        }


def _print(text, stream):
    """print(), but never crash on a stream that can't encode "→" or emoji (a Windows pipe)."""
    try:
        print(text, file=stream, flush=True)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        print(text.encode(encoding, "replace").decode(encoding), file=stream)


def _wants_fancy():
    if not sys.stderr.isatty():
        return False
    return not any(os.environ.get(name) for name in ("NO_COLOR", "CI", "CLAUDECODE"))


class Output:
    def __init__(self, json_mode=False):
        self.json_mode = json_mode
        self.fancy = not json_mode and _wants_fancy()

    def say(self, plain, fancy=None):
        """A message for the person (stderr). `fancy` is used on an interactive terminal."""
        _print(fancy if (self.fancy and fancy) else plain, sys.stderr)

    def data(self, text):
        """Data for scripts (stdout). Suppressed in --json mode, where only the result prints."""
        if not self.json_mode:
            _print(text, sys.stdout)

    def result(self, command, payload):
        if self.json_mode:
            print(json.dumps(
                {"format_version": FORMAT_VERSION, "command": command, "ok": True, **payload},
                indent=2,
            ))

    def failure(self, command, failure):
        if self.json_mode:
            print(json.dumps(
                {
                    "format_version": FORMAT_VERSION,
                    "command": command,
                    "ok": False,
                    "exit_code": failure.exit_code,
                    "error": failure.as_dict(),
                    **failure.details,
                },
                indent=2,
            ))
        else:
            self.say(
                "error: {}".format(failure.message),
                "Hold up!! 👮🚨 {}".format(failure.message),
            )
            if failure.hint:
                self.say("hint: {}".format(failure.hint))
