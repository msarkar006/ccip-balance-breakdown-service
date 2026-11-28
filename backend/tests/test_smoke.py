from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.conftest import _BACKEND


def test_health_and_migration_head(client: TestClient, db_session: Session) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/health/ready").status_code == 200

    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    heads = ScriptDirectory.from_config(config).get_heads()
    assert len(heads) == 1
    applied = db_session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert applied == heads[0]
