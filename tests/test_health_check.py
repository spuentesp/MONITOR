from __future__ import annotations


def test_health_check_imports():
    # Ensure script imports and has main()
    import scripts.health_check as hc

    assert callable(hc.main)
