# Shared by every test file. Extend it; never add a second database setup.
import os
import sqlite3
import tempfile
from pathlib import Path

# 1. Configuration BEFORE anything imports the app: committed dev.env, then test overrides.
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break
_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["SEED_ENABLED"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import app.models  # noqa: E402, F401 - registers every model on Base
from app.database import build_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402  (last: `import app.models` rebinds the name `app`)
from app.seed_data.users import PERSONAS  # noqa: E402

engine = build_engine(os.environ["DATABASE_URL"])
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _copy_database(source: Path, target: Path) -> None:
    engine.dispose()
    src, dst = sqlite3.connect(source), sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()


@pytest.fixture(scope="session")
def _template_db() -> Path:
    """Schema built ONCE per run from the real Alembic migrations; each test gets a copy."""
    from alembic.config import Config

    from alembic import command

    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(config, "head")
    path = _DB_FILE.with_name("template.db")
    _copy_database(_DB_FILE, path)
    return path


@pytest.fixture(autouse=True)
def _fresh_database(_template_db: Path) -> None:
    _copy_database(_template_db, _DB_FILE)
    from app.middleware.metrics import metrics

    metrics.reset()
    from app.services.login_rate_limiter import login_rate_limiter

    login_rate_limiter.reset()


@pytest.fixture(scope="session")
def _seeded_file(_template_db: Path) -> Path:
    """The demo seed runs ONCE per run (available once the seed task adds `app.seed`)."""
    from app.seed import seed_database  # type: ignore[import-not-found]

    path = _DB_FILE.with_name("seeded.db")
    _copy_database(_template_db, path)
    seed_engine = create_engine(f"sqlite:///{path.as_posix()}")
    with sessionmaker(bind=seed_engine)() as session:
        seed_database(session)
        session.commit()
    seed_engine.dispose()
    return path


@pytest.fixture
def seeded(_seeded_file: Path) -> None:
    """List before `client` / `db_session`: the test gets a copy of the seeded database."""
    _copy_database(_seeded_file, _DB_FILE)


@pytest.fixture
def db_session() -> Session:  # type: ignore[misc]
    session = TestingSession()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:  # type: ignore[misc]
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client  # type: ignore[misc]
    app.dependency_overrides.clear()


def login(client: TestClient, persona: str = "customer01") -> dict[str, str]:
    """Sign in through the REAL auth endpoint with the REAL seed credentials; return auth headers.

    Needs the `seeded` fixture (or factory-created users with the same credentials) and the auth router
    from the identity task.
    """
    creds = PERSONAS[persona]
    response = client.post("/api/v1/auth/login", json={"username": creds.username, "password": creds.password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


@pytest.fixture
def auth_headers(client: TestClient):  # type: ignore[no-untyped-def]
    """Factory: `auth_headers("customer01")` -> Authorization header for that persona."""

    def _headers(persona: str = "customer01") -> dict[str, str]:
        return login(client, persona)

    return _headers
