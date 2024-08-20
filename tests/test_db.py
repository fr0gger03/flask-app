import io
import pytest
import sqlalchemy

from pathlib import Path
from testcontainers.postgres import PostgresContainer
from src.app import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_docker_run_postgres_with_sqlalchemy():
    postgres_container = PostgresContainer("postgres:16.3-bookworm")
    with postgres_container as postgres:
        engine = sqlalchemy.create_engine(postgres.get_connection_url())
        with engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("select version()"))
            for row in result:
                assert row[0].lower().startswith("postgresql 16.3")


# This is a feature in the generic DbContainer class
# but it can't be tested on its own
# so is tested in various database modules
def test_quoted_password():
    user = "postgres"
    password = "postgres"
    quoted_password = "postgres"
    driver = "psycopg2"
    port = "5432"

    kwargs = {
        "driver": driver,
        "user": user,
        "password": password,
        "port":port
    }
    with PostgresContainer("postgres:16.3", **kwargs) as container:
        port = container.get_exposed_port(5432)
        host = container.get_container_host_ip()
        expected_url = f"postgresql+{driver}://{user}:{quoted_password}@{host}:{port}/test"

        url = container.get_connection_url()
        assert url == expected_url

        with sqlalchemy.create_engine(expected_url).begin() as connection:
            connection.execute(sqlalchemy.text("select 1=1"))

        raw_pass_url = f"postgresql+{driver}://{user}:{password}@{host}:{port}/test"
        with pytest.raises(Exception):
            # it raises ValueError, but auth (OperationalError) = more interesting
            with sqlalchemy.create_engine(raw_pass_url).begin() as connection:
                connection.execute(sqlalchemy.text("select 1=1"))


def test_show_how_to_initialize_db_via_initdb_dir():
    postgres_container = PostgresContainer("postgres:16.3-bookworm")
    script = Path(__file__).parent / "src" / "sql" / "init-user-db.sh"
    postgres_container.with_volume_mapping(host=str(script), container=f"/docker-entrypoint-initdb.d/{script.name}")

    insert_query = "insert into example(name, description) VALUES ('sally', 'sells seashells');"
    select_query = "select id, name, description from example;"

    with postgres_container as postgres:
        engine = sqlalchemy.create_engine(postgres.get_connection_url())
        with engine.begin() as connection:
            connection.execute(sqlalchemy.text(insert_query))
            result = connection.execute(sqlalchemy.text(select_query))
            result = result.fetchall()
            assert len(result) == 1
            assert result[0] == (1, "sally", "sells seashells")


def test_login_post(client):
    '''Testing login post - this will probably require Testcontainers with username and password in the database to test correctly...'''
    response = client.post('/login', data=dict(username='testuser', password='testpass'))
    assert b'Login successful' in response.data  # Adjust according to your actual response content


def test_upload_get(client):
    response = client.get('/upload')
    assert response.status_code == 302
    assert b'Upload Excel File' in response.data  # Adjust according to your actual response content


def test_upload_post(client):
    data = {
        'file': (io.BytesIO(b"some initial text data"), 'test.txt')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert b'File uploaded successfully' in response.data  # Adjust according to your actual response content
