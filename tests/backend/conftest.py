"""Configuración común: las pruebas nunca escriben en la base de datos real del usuario."""

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolated_data_dir(tmp_path_factory):
    import os

    path = tmp_path_factory.mktemp("scriptlens-data")
    os.environ["SCRIPTLENS_DATA_DIR"] = str(path)
    from backend.core import config

    original = config.default_data_dir
    config.default_data_dir = lambda: path
    yield path
    config.default_data_dir = original
