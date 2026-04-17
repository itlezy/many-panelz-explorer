"""Tests for runtime trace configuration and JSON output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from many_panelz_explorer.runtime_trace import (
    TRACE_JSON_ENV_VAR,
    RuntimeTraceRecorder,
    configure_runtime_trace,
    flush_runtime_trace,
    resolve_runtime_trace_configuration,
    trace_span,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_runtime_trace_configuration_prefers_cli_flag(tmp_path: Path) -> None:
    """CLI trace output should override the environment fallback."""

    env_path = tmp_path / "env-trace.json"
    cli_path = tmp_path / "cli-trace.json"
    argv, output_path = resolve_runtime_trace_configuration(
        [
            "many-panelz-explorer",
            "--trace-json",
            str(cli_path),
            "--platform",
            "windows",
        ],
        env={TRACE_JSON_ENV_VAR: str(env_path)},
    )
    assert argv == ["many-panelz-explorer", "--platform", "windows"]
    assert output_path == cli_path


def test_resolve_runtime_trace_configuration_accepts_equals_syntax(
    tmp_path: Path,
) -> None:
    """The ``--trace-json=...`` form should strip only the trace flag."""

    cli_path = tmp_path / "equals-trace.json"
    argv, output_path = resolve_runtime_trace_configuration(
        [
            "many-panelz-explorer",
            f"--trace-json={cli_path}",
            "--style",
            "fusion",
        ],
        env={},
    )
    assert argv == ["many-panelz-explorer", "--style", "fusion"]
    assert output_path == cli_path


def test_resolve_runtime_trace_configuration_rejects_missing_path() -> None:
    """The parser should reject ``--trace-json`` without a value."""

    try:
        resolve_runtime_trace_configuration(["many-panelz-explorer", "--trace-json"])
    except ValueError as exc:
        assert "--trace-json requires a file path." in str(exc)
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected --trace-json without a value to fail.")


def test_runtime_trace_recorder_writes_chrome_trace_json(tmp_path: Path) -> None:
    """Recorder output should follow the Chrome Trace Event JSON shape."""

    output_path = tmp_path / "trace.json"
    recorder = RuntimeTraceRecorder(output_path)
    with recorder.span(
        "unit.runtime_trace",
        "tests",
        args={"item_count": 3, "enabled": True},
    ):
        pass

    written_path = recorder.flush()
    payload = json.loads(written_path.read_text(encoding="utf-8"))
    trace_events = payload["traceEvents"]
    assert payload["displayTimeUnit"] == "ms"
    assert any(event["name"] == "process_name" for event in trace_events)
    span_events = [
        event for event in trace_events if event.get("name") == "unit.runtime_trace"
    ]
    assert len(span_events) == 1
    span_event = span_events[0]
    assert span_event["ph"] == "X"
    assert span_event["cat"] == "tests"
    assert span_event["dur"] >= 0
    assert span_event["args"] == {"item_count": 3, "enabled": True}


def test_trace_span_records_into_active_runtime_trace(tmp_path: Path) -> None:
    """Global helper spans should write into the configured recorder."""

    output_path = tmp_path / "active-trace.json"
    configure_runtime_trace(None)
    try:
        configure_runtime_trace(output_path)
        with trace_span("unit.global_trace", "tests", args={"count": 1}):
            pass
        written_path = flush_runtime_trace()
    finally:
        configure_runtime_trace(None)

    assert written_path is not None
    assert written_path == output_path
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    span_events = [
        event
        for event in payload["traceEvents"]
        if event.get("name") == "unit.global_trace"
    ]
    assert len(span_events) == 1
