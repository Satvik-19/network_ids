"""conftest.py — backend test session setup.

Sandboxes the SQLite DB to a throwaway temp file so Phase-3 replay tests never
touch the developer's data/network_ids.db. NETWORK_IDS_DB must be set before
database.py is imported (module-level engine binding), and conftest is imported
before any test module by pytest.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="nids_tests_"))
os.environ["NETWORK_IDS_DB"] = str(_tmp / "test.db")
os.environ["NIDS_TEST_TMP"] = str(_tmp)

from backend.app.db.database import DB_PATH, init_db  # noqa: E402

init_db()


def pytest_configure(config):
    config.option.continue_on_collection_errors = True


import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def sandboxed_db():
    yield DB_PATH
    try:
        Path(os.environ["NIDS_TEST_TMP"]).rmdir()
    except OSError:
        pass