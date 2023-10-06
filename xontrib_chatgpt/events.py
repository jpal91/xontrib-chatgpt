"""Events for xontrib_chatgpt."""
from xonsh.built_ins import XonshSession
from xontrib_chatgpt.chatmanager import ChatManager

chat_events = [
    (
        "on_chat_create",
        """
        on_chat_create(inst: ChatGPT) -> None

        Fired when new chat is created. Passes the new instance to be added to
        the chat manager.
        """,
    ),
    (
        "on_chat_destroy",
        """
        on_chat_destroy(inst: ChatGPT) -> None

        Fired when chat is destroyed. Passes the instance to be removed from
        the chat manager.
        """,
    ),
    (
        "on_chat_used",
        """
        on_chat_used(inst: ChatGPT) -> None

        Fires when chat is used, i.e. chatgpt is called. Passes the instance
        of the chat instance to update the current chat for the manager.
        """,
    ),
]


def add_events(xsh: XonshSession, cm: ChatManager):
    events = xsh.builtins.events

    for c in chat_events:
        events.doc(*c)

    events.on_chat_create(lambda *_, **kw: cm.on_chat_create_handler(**kw))
    events.on_chat_destroy(lambda *_, **kw: cm.on_chat_destroy_handler(**kw))
    events.on_chat_used(lambda *_, **kw: cm.on_chat_used_handler(**kw))


def rm_events(xsh: XonshSession):
    events = xsh.builtins.events

    for c in chat_events:
        delattr(events, c[0])
