import pytest
from xonsh.xontribs import xontribs_unload, xontribs_load

@pytest.fixture
def loaded_session(xession):
    xontribs_load(["chatgpt"])
    yield xession
    xontribs_unload(["chatgpt"])

def test_it_loads(loaded_session):
    assert "chatgpt" in loaded_session.aliases
    assert 'chatgpt?' in loaded_session.aliases

def test_it_unloads(loaded_session):
    xontribs_unload(["chatgpt"])
    assert "chatgpt" not in loaded_session.aliases
    assert 'chatgpt?' not in loaded_session.aliases