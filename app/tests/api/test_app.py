import json
import pytest
from app.settings.settings import config
from app.tests.api.test_app_constants import RUN_INTERPRETATION, RUN_DICT
from app.api.app import app


@pytest.fixture
def client():
    app.config.update(config)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def image_test():
    file = 'app/tests/img/small.png'
    data = {
        'file': (open(file, 'rb'), file),
    }
    return data


@pytest.fixture
def image_run():
    # high quality picture
    file = 'app/tests/img/run.jpeg'
    data = {
        'file': (open(file, 'rb'), file),
    }
    return data


@pytest.fixture
def image_run_strict():
    # picture is not so clear
    file = 'app/tests/img/run_unclear.jpeg'
    data = {
        'threshold': '1',
        'file': (open(file, 'rb'), file),
    }
    return data


@pytest.fixture
def invalid_file():
    # picture is not so clear
    file = 'app/tests/img/file.strange'
    data = {
        'file': (open(file, 'rb'), file),
    }
    return data

