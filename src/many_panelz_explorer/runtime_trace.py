"""Optional Chrome Trace JSON profiling hooks for runtime diagnostics."""

from __future__ import annotations

import atexit
import json
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

TRACE_JSON_ENV_VAR = "MANY_PANELZ_TRACE_JSON"

type TraceArgumentValue = str | int | float | bool | None
type TraceArguments = Mapping[str, TraceArgumentValue]
type _TracePhase = Literal["M", "X"]


class _TraceEvent(TypedDict, total=False):
    """Represent one Chrome Trace Event JSON payload entry."""

    name: str
    cat: str
    ph: _TracePhase
    ts: float
    dur: float
    pid: int
    tid: int
    args: dict[str, TraceArgumentValue]


class RuntimeTraceRecorder:
    """Collect runtime spans and persist them as Chrome Trace Event JSON."""

    def __init__(self, output_path: Path) -> None:
        """Store the trace destination and initialize metadata events.

        Args:
            output_path: JSON file written when the session shuts down.
        """

        self.output_path = Path(output_path)
        self._events: list[_TraceEvent] = []
        self._lock = threading.RLock()
        self._start_ns = time.perf_counter_ns()
        self._pid = os.getpid()
        self._known_threads: set[int] = set()
        self._flushed = False
        self._record_process_metadata()
        self._record_thread_metadata(threading.get_native_id(), "MainThread")

    def record_complete(
        self,
        name: str,
        category: str,
        *,
        started_ns: int,
        finished_ns: int | None = None,
        args: TraceArguments | None = None,
    ) -> None:
        """Record one complete span event.

        Args:
            name: Span label shown in trace viewers.
            category: Chrome trace category string.
            started_ns: Monotonic start timestamp from ``time.perf_counter_ns``.
            finished_ns: Optional end timestamp; defaults to "now".
            args: Optional scalar metadata attached to the span.
        """

        if self._flushed:
            return
        end_ns = time.perf_counter_ns() if finished_ns is None else finished_ns
        thread_id = threading.get_native_id()
        thread_name = threading.current_thread().name or f"Thread-{thread_id}"
        with self._lock:
            self._record_thread_metadata(thread_id, thread_name)
            self._events.append(
                {
                    "name": str(name),
                    "cat": str(category),
                    "ph": "X",
                    "ts": self._relative_microseconds(started_ns),
                    "dur": self._duration_microseconds(started_ns, end_ns),
                    "pid": self._pid,
                    "tid": thread_id,
                    "args": self._normalized_args(args),
                }
            )

    @contextmanager
    def span(
        self,
        name: str,
        category: str,
        *,
        args: TraceArguments | None = None,
    ) -> Iterator[None]:
        """Measure one scoped runtime span.

        Args:
            name: Span label shown in trace viewers.
            category: Chrome trace category string.
            args: Optional scalar metadata attached to the span.

        Yields:
            None.
        """

        started_ns = time.perf_counter_ns()
        try:
            yield
        finally:
            self.record_complete(
                name,
                category,
                started_ns=started_ns,
                finished_ns=time.perf_counter_ns(),
                args=args,
            )

    def flush(self) -> Path:
        """Write the accumulated trace file once and return its path."""

        with self._lock:
            if self._flushed:
                return self.output_path
            payload = {
                "displayTimeUnit": "ms",
                "traceEvents": list(self._events),
            }
            self._flushed = True

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        self.output_path.write_text(
            f"{serialized}\n",
            encoding="utf-8",
            newline="\n",
        )
        return self.output_path

    def _record_process_metadata(self) -> None:
        """Emit the process-name metadata event."""

        self._events.append(
            {
                "name": "process_name",
                "ph": "M",
                "pid": self._pid,
                "tid": 0,
                "args": {"name": "many-panelz-explorer"},
            }
        )

    def _record_thread_metadata(self, thread_id: int, thread_name: str) -> None:
        """Emit thread-name metadata once for one runtime thread."""

        if thread_id in self._known_threads:
            return
        self._known_threads.add(thread_id)
        self._events.append(
            {
                "name": "thread_name",
                "ph": "M",
                "pid": self._pid,
                "tid": int(thread_id),
                "args": {"name": str(thread_name)},
            }
        )

    def _normalized_args(
        self,
        args: TraceArguments | None,
    ) -> dict[str, TraceArgumentValue]:
        """Return JSON-safe scalar arguments for one span."""

        if args is None:
            return {}
        return {str(key): value for key, value in args.items()}

    def _relative_microseconds(self, timestamp_ns: int) -> float:
        """Return one timestamp relative to process start in microseconds."""

        return (timestamp_ns - self._start_ns) / 1_000.0

    def _duration_microseconds(self, started_ns: int, finished_ns: int) -> float:
        """Return one span duration in microseconds."""

        return max(0.0, (finished_ns - started_ns) / 1_000.0)


_active_trace_recorder: RuntimeTraceRecorder | None = None
_atexit_flush_registered = False


def resolve_runtime_trace_configuration(
    argv: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[list[str], Path | None]:
    """Parse CLI and environment configuration for runtime tracing.

    Args:
        argv: Raw command-line arguments, including argv[0].
        env: Optional environment variable mapping used for tests.

    Returns:
        Tuple of ``(argv_without_trace_flags, output_path_or_none)``.

    Raises:
        ValueError: If ``--trace-json`` is provided without a usable path.
    """

    env_map = os.environ if env is None else env
    output_path = _trace_output_path_from_env(env_map)
    remaining = [str(part) for part in argv[:1]]
    index = 1
    while index < len(argv):
        token = str(argv[index])
        if token == "--trace-json":
            if index + 1 >= len(argv):
                raise ValueError("--trace-json requires a file path.")
            output_path = _coerce_trace_output_path(argv[index + 1])
            index += 2
            continue
        if token.startswith("--trace-json="):
            output_path = _coerce_trace_output_path(token.removeprefix("--trace-json="))
            index += 1
            continue
        remaining.append(token)
        index += 1
    return remaining, output_path


def configure_runtime_trace(
    output_path: Path | None,
) -> RuntimeTraceRecorder | None:
    """Enable or disable the process-wide runtime trace recorder.

    Args:
        output_path: Target JSON path, or ``None`` to disable tracing.

    Returns:
        The active recorder when tracing is enabled, else ``None``.
    """

    global _active_trace_recorder, _atexit_flush_registered
    existing = _active_trace_recorder
    if output_path is None:
        if existing is not None:
            existing.flush()
        _active_trace_recorder = None
        return None
    if existing is not None and existing.output_path != output_path:
        existing.flush()
    recorder = RuntimeTraceRecorder(output_path)
    _active_trace_recorder = recorder
    if not _atexit_flush_registered:
        atexit.register(flush_runtime_trace)
        _atexit_flush_registered = True
    return recorder


def active_runtime_trace() -> RuntimeTraceRecorder | None:
    """Return the current process-wide runtime trace recorder, if enabled."""

    return _active_trace_recorder


def flush_runtime_trace() -> Path | None:
    """Flush the active runtime trace recorder, if one exists."""

    recorder = _active_trace_recorder
    if recorder is None:
        return None
    return recorder.flush()


@contextmanager
def trace_span(
    name: str,
    category: str,
    *,
    args: TraceArguments | None = None,
) -> Iterator[None]:
    """Measure one span against the active runtime trace recorder.

    Args:
        name: Span label shown in trace viewers.
        category: Chrome trace category string.
        args: Optional scalar metadata attached to the span.

    Yields:
        None.
    """

    recorder = active_runtime_trace()
    if recorder is None:
        yield
        return
    with recorder.span(name, category, args=args):
        yield


def _trace_output_path_from_env(env: Mapping[str, str]) -> Path | None:
    """Return the configured trace path from the environment, if present."""

    raw_value = str(env.get(TRACE_JSON_ENV_VAR, "")).strip()
    if not raw_value:
        return None
    return _coerce_trace_output_path(raw_value)


def _coerce_trace_output_path(value: str) -> Path:
    """Normalize one trace output path from CLI or environment input."""

    normalized = str(value).strip()
    if not normalized:
        raise ValueError("--trace-json requires a file path.")
    return Path(normalized).expanduser()
