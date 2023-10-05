"""chatgpt xontrib"""
from xonsh.built_ins import XonshSession
from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.chatmanager import ChatManager


__all__ = ()


def _load_xontrib_(xsh: XonshSession, **_):

    xsh.aliases["chatgpt"] = lambda args, stdin=None: ChatGPT.fromcli(args, stdin)
    xsh.aliases["chatgpt?"] = lambda *_, **__: xsh.help(ChatGPT)
    
    CM = ChatManager()
    xsh.aliases["chat-manager"] = lambda args, stdin=None: CM(args, stdin)

    if 'abbrevs' in xsh.ctx:
        xsh.ctx['abbrevs']['cm'] = 'chat-manager'

    return {"ChatGPT": ChatGPT}


def _unload_xontrib_(xsh: XonshSession, **_):
    del xsh.aliases["chatgpt"]
    del xsh.aliases["chatgpt?"]
    del xsh.aliases["chat-manager"]

    if 'abbrevs' in xsh.ctx:
        del xsh.ctx['abbrevs']['cm']
