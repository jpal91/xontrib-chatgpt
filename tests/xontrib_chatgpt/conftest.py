import pytest
from xontrib_chatgpt.events import chat_events

@pytest.fixture
def cm_events(xession):
    events = xession.builtins.events
    for c in chat_events:
        events.doc(*c)
    yield events