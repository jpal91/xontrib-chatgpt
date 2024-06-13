import shutil
import pytest
from xontrib_chatgpt.events import chat_events


@pytest.fixture
def cm_events(xession):
    events = xession.builtins.events
    for c in chat_events:
        events.doc(*c)
    yield events


@pytest.fixture(scope="module")
def temp_home(tmpdir_factory):
    home = tmpdir_factory.mktemp("home")
    home.mkdir("expected")
    home.mkdir("saved")
    data_dir = home.mkdir("data_dir")
    data_dir.mkdir("chatgpt")
    fixtures = [
        "color_convo.txt",
        "no_color_convo.txt",
        "no_color_convo2.txt",
        "convo.json",
        "convo2.json",
        "long_convo.txt",
    ]
    for f in fixtures:
        shutil.copy(f"tests/fixtures/{f}", f"{home}/expected/{f}")
    shutil.copy(
        f"tests/fixtures/no_color_convo.txt", f"{data_dir}/chatgpt/no_color_convo.txt"
    )
    yield home
