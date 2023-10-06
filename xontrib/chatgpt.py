"""chatgpt xontrib"""
from xonsh.built_ins import XonshSession
from xonsh.completers.completer import add_one_completer, remove_completer

from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.chatmanager import ChatManager
from xontrib_chatgpt.events import add_events, rm_events
from xontrib_chatgpt.completers import cm_completer


__all__ = ()


def _load_xontrib_(xsh: XonshSession, **_):
    xsh.aliases["chatgpt"] = lambda args, stdin=None: ChatGPT.fromcli(args, stdin)
    xsh.aliases["chatgpt?"] = lambda *_, **__: xsh.help(ChatGPT)

    cm = ChatManager()
    xsh.aliases["chat-manager"] = lambda args, stdin=None: cm(args, stdin)
    xsh.aliases["chat-manager?"] = "chat-manager help"

    add_events(xsh, cm)

    if "abbrevs" in xsh.ctx:
        xsh.ctx["abbrevs"]["cm"] = "chat-manager"
    
    add_one_completer("chat-manager", cm_completer, loc="start")

    return {"ChatGPT": ChatGPT, "chat_manager": cm}


def _unload_xontrib_(xsh: XonshSession, **_):
    del xsh.aliases["chatgpt"]
    del xsh.aliases["chatgpt?"]
    del xsh.aliases["chat-manager"]

    rm_events(xsh)

    if "abbrevs" in xsh.ctx:
        del xsh.ctx["abbrevs"]["cm"]
    
    remove_completer("chat-manager")
