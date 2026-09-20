"""Test fixtures — isolated temp DB, alembic migrations, TestClient.

The env vars MUST be set before importing app.* (settings are cached).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_tmp = Path(tempfile.mkdtemp(prefix="alems-test-"))
os.environ["ALEMS_DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["ALEMS_DATA_DIR"] = str(_tmp / "data")
os.environ["ALEMS_BACKUPS_DIR"] = str(_tmp / "backups")
os.environ["ALEMS_EXPORTS_DIR"] = str(_tmp / "exports")
os.environ["ALEMS_IMPORTS_DIR"] = str(_tmp / "imports")

# make backend/ importable
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


@pytest.fixture(scope="session")
def _migrated():
    """Run alembic upgrade head once for the whole session."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(scope="session")
def client(_migrated):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    """A fresh session on the test DB."""
    from app.db.session import get_session_factory

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
