from __future__ import annotations

from core.domain.base_model import BaseModel


def test_base_model_instantiation():
    class X(BaseModel):
        a: int

    x = X(a=1)
    assert x.a == 1
