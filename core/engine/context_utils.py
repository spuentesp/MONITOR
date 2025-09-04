from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine.tools import ToolContext


def as_dry_run(ctx: ToolContext, dry: bool = True) -> ToolContext:
    """Return a copy of ToolContext with dry_run set to the requested value.

    Falls back to mutating the original if dataclasses.replace is not applicable.
    """
    try:
        return replace(ctx, dry_run=dry)
    except Exception:
        try:
            ctx.dry_run = dry
        except Exception:
            pass
        return ctx
