"""Optional LLM tracing with a self-hosted Langfuse.

Off unless LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set (see
observability/setup_env.py). When on, every assistant turn becomes a trace:
model calls with tokens and latency, each tool call with its input and
result, grouped by conversation (session) and user.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from app.core.config import settings


@dataclass
class Trace:
    """Callbacks to pass in a LangChain config, plus the trace id (None
    when tracing is off)."""

    callbacks: list = field(default_factory=list)
    trace_id: str | None = None
    span: Any = None

    def finish(self, output: Any) -> None:
        if self.span is not None:
            self.span.update(output=output)


@lru_cache
def get_langfuse():
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None

    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


@contextmanager
def traced(
    name: str,
    *,
    user_id: int,
    session_id: str,
    input: Any,
    tags: list[str] | None = None,
) -> Iterator[Trace]:
    langfuse = get_langfuse()
    if langfuse is None:
        yield Trace()
        return

    from langfuse import propagate_attributes
    from langfuse.langchain import CallbackHandler

    with langfuse.start_as_current_observation(name=name, as_type="agent", input=input) as span:
        with propagate_attributes(
            user_id=str(user_id),
            session_id=session_id,
            tags=tags or [],
            trace_name=name,
        ):
            try:
                yield Trace(
                    callbacks=[CallbackHandler()],
                    trace_id=langfuse.get_current_trace_id(),
                    span=span,
                )
            except Exception as e:
                # A failed turn shows up as an error in Langfuse, with the
                # reason, instead of a trace that just has no output.
                span.update(level="ERROR", status_message=f"{type(e).__name__}: {e}"[:500])
                raise


def score(trace_id: str | None, name: str, value: float, comment: str | None = None) -> None:
    """Attach an evaluation score to a trace, e.g. from the eval runner."""

    langfuse = get_langfuse()
    if langfuse is None or trace_id is None:
        return

    langfuse.create_score(trace_id=trace_id, name=name, value=value, comment=comment)


def flush() -> None:
    langfuse = get_langfuse()
    if langfuse is not None:
        langfuse.flush()
