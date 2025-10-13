import os
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture
def app():
    os.environ["FLASK_ENV"] = "testing"
    app = create_app("testing")
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    _db.drop_all()
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()
