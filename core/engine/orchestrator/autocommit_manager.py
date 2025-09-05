"""Auto-commit management functions."""

from __future__ import annotations

from typing import Any

from core.engine.tools import ToolContext


def autocommit_stats() -> dict[str, Any]:
    """Return statistics about the auto-commit worker and staging store."""
    from core.config.tool_context_builder import (
        _AUTOCOMMIT_QUEUE,
        _AUTOCOMMIT_WORKER,
        _IDEMPOTENCY_SET,
    )

    worker_active = _AUTOCOMMIT_WORKER is not None
    queue_size = _AUTOCOMMIT_QUEUE.qsize() if _AUTOCOMMIT_QUEUE else 0
    idempotency_size = len(_IDEMPOTENCY_SET) if _IDEMPOTENCY_SET else 0

    return {
        "worker_active": worker_active,
        "queue_size": queue_size,
        "idempotency_set_size": idempotency_size,
    }


def flush_staging(ctx: ToolContext) -> dict[str, Any]:
    """Flush all staged changes to persistent storage."""
    if not hasattr(ctx, "staging") or not ctx.staging:
        return {"error": "No staging store available"}

    if not hasattr(ctx, "recorder") or not ctx.recorder:
        return {"error": "No recorder available"}

    pending = ctx.staging.peek_all()
    if not pending:
        return {"message": "No staged changes to flush"}

    # Process all staged items
    results = []
    for item in pending:
        try:
            # Commit via recorder
            result = ctx.recorder.commit_deltas(**item)
            results.append(result)
            # Remove from staging after successful commit
            ctx.staging.pop()
        except Exception as e:
            results.append({"error": str(e), "item": item})
            break  # Stop on first error to maintain consistency

    return {
        "flushed": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        "results": results,
    }
