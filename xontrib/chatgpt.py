"""chatgpt xontrib"""
from xonsh.built_ins import XonshSession
from xontrib_chatgpt.chatgpt import ChatGPT


__all__ = ()


def _load_xontrib_(xsh: XonshSession, **_):
    xsh.aliases["chatgpt"] = lambda args, stdin=None: ChatGPT.fromcli(args, stdin)
    xsh.aliases["chatgpt?"] = lambda *_, **__: xsh.help(ChatGPT)

    return {"ChatGPT": ChatGPT}


def _unload_xontrib_(xsh: XonshSession, **_):
    del xsh.aliases["chatgpt"]
    del xsh.aliases["chatgpt?"]
