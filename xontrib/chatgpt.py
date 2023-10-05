"""chatgpt xontrib"""
from xonsh.built_ins import XonshSession
from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.chatmanager import ChatManager
from xontrib_chatgpt.events import add_events, rm_events


__all__ = ()


def _load_xontrib_(xsh: XonshSession, **_):

    xsh.aliases["chatgpt"] = lambda args, stdin=None: ChatGPT.fromcli(args, stdin)
    xsh.aliases["chatgpt?"] = lambda *_, **__: xsh.help(ChatGPT)
    
    cm = ChatManager()
    xsh.aliases["chat-manager"] = lambda args, stdin=None: cm(args, stdin)

    add_events(xsh, cm)

    if 'abbrevs' in xsh.ctx:
        xsh.ctx['abbrevs']['cm'] = 'chat-manager'

    return {"ChatGPT": ChatGPT, 'chatmanager': cm}


def _unload_xontrib_(xsh: XonshSession, **_):
    del xsh.aliases["chatgpt"]
    del xsh.aliases["chatgpt?"]
    del xsh.aliases["chat-manager"]

    rm_events(xsh)

    if 'abbrevs' in xsh.ctx:
        del xsh.ctx['abbrevs']['cm']
