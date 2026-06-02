"""Shared pytest fixtures for BMG-Harmony tests."""

import pytest

from server.store import init_db


@pytest.fixture
def tmp_db(tmp_path):
    """Yield an open SQLite connection pointed at a temp store.

    Calls con.close() on teardown.
    """
    db_path = str(tmp_path / "harmony.sqlite")
    con = init_db(db_path)
    yield con
    con.close()
