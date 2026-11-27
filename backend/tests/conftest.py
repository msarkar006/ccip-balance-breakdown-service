"""
Shared test fixtures for the backend test suite.
"""
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configuration BEFORE importing app modules
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break

# Set test database URL
_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

# Now import app modules
import app.models  # noqa: F401
from app.core.database import Base, get_db

# Create test engine and session factory
engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh database schema before each test and clean up after."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """
    Provide a database session for tests.
    
    Returns:
        Session: SQLAlchemy database session
    """
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """
    Provide a TestClient with database dependency override.
    
    Args:
        db_session: Database session fixture
        
    Returns:
        TestClient: FastAPI test client
    """
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, db_session):
    """
    Provide an authenticated test client logged in as admin.
    
    Args:
        client: Base test client
        db_session: Database session
        
    Returns:
        TestClient: Authenticated test client
    """
    from app.core.security import hash_password
    from app.models.app_user import AppUser
    from app.models.customer import Customer

    # Create customer (required for ownership verification)
    # Note: customer.email must match user.email for ownership checks
    customer = Customer(
        id=1,
        external_customer_id="CUST-TEST-001",
        masked_name="Test Customer",
        email="admin@example.com",
        phone_last_four="9000"
    )
    db_session.add(customer)
    db_session.commit()

    # Create admin user
    admin = AppUser(
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"

    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    return client
