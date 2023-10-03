import weakref
from collections import defaultdict
from typing import Optional, Union
from xonsh.built_ins import XSH
from xonsh.events import events
from xontrib_chatgpt.chatgpt import ChatGPT

class ChatManager:
    """Class to manage multiple chats"""

    def __init__(self):
        self._instances: dict[int, dict[str, Union[ChatGPT, str]]] = defaultdict(dict)
        self._current: Optional[int] = None

    def __call__(self, args, stdin=None):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass

    def add(self, chat):
        pass

    def ls(self):
        pass

    def load(self, chat):
        pass

    def save(self, chat):
        pass

    def help(self, tgt):
        pass

    def _update_inst_dict(self):
        """Finds all active instances (active convos) in the global space and updates the internal dict"""
        for key, inst in XSH.ctx.copy().items():
            if isinstance(inst, ChatGPT):
                
                self._instances[hash(inst)] = {
                    'name': key,
                    'alias': inst.alias,
                    'inst': weakref.proxy(inst),
                }
        
        if self._current not in self._instances:
            self._current = None
    
    def _on_chat_create(self, inst_hash: int) -> None:
        """Handler for on_chat_create. Updates the internal dict with the new chat instance."""
        self._current = inst_hash
        if inst_hash not in self._instances:
            self._update_inst_dict()
    
    def _on_chat_destroy(self, inst_hash: int) -> None:
        """Handler for on_chat_destroy. Removes the chat instance from the internal dict."""
        if inst_hash in self._instances:
            del self._instances[inst_hash]
        
        if inst_hash == self._current:
            self._current = None
    
    def _on_chat_change(self, inst_hash: int) -> None:
        """Handler for on_chat_change. Updates the current chat instance."""
        self._current = inst_hash