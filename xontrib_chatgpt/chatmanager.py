import os
import weakref
from collections import defaultdict
from typing import Optional, Union
from xonsh.built_ins import XSH
from xonsh.lazyasd import LazyObject
from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.lazyobjs import _FIND_NAME_REGEX

FIND_NAME_REGEX = LazyObject(_FIND_NAME_REGEX, globals(), 'FIND_NAME_REGEX')

class ChatManager:
    """Class to manage multiple chats"""

    def __init__(self):
        self._instances: dict[int, dict[str, Union[str, ChatGPT]]] = defaultdict(dict)
        self._current: Optional[int] = None

    def __call__(self, args, stdin=None):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass

    def add(self, chat_name: str) -> str:
        """Create new chat instance"""
        inst = ChatGPT(alias=chat_name, managed=True)
        XSH.ctx[chat_name] = inst
        self._instances[hash(inst)]['name'] = chat_name
        return f'Created new chat {chat_name}'

    def ls(self, saved: bool = False) -> None:
        """List all active chats or saved chats"""
        if saved:
            print('Saved chats:')
            [print(f'  {f}') for f in self._find_saved()]
            return
        
        for inst in self._instances.values():
            print(f'Name: {inst["name"]}')
            print(str(inst['inst']))
            print('')

    def load(self, path_or_name: str) -> str:
        """Load a conversation from a path or a saved chat name"""
        if os.path.exists(path_or_name):
            path, name = path_or_name, FIND_NAME_REGEX.sub(r'\1', os.path.basename(path_or_name))
        else:
            path, name = self._find_path_from_name(path_or_name)
        
        inst = ChatGPT.fromconvo(path, alias=name, managed=True)
        XSH.ctx[name] = inst
        self._instances[hash(inst)]['name'] = name

        return f'Loaded chat {name} from {path}'

    def save(self, chat):
        pass

    def help(self, tgt):
        pass

    def _find_saved(self) -> list[str]:
        def_dir = os.path.join(XSH.env['XONSH_DATA_DIR'], 'chatgpt')
        return [f for f in os.listdir(def_dir) if os.path.isfile(os.path.join(def_dir, f))]
    
    def _find_path_from_name(self, name: str) -> tuple[str, str]:
        def_dir = XSH.env['XONSH_DATA_DIR']
        saved = self._find_saved()

        if name in saved:
            return os.path.join(def_dir, 'chatgpt', name), FIND_NAME_REGEX.sub(r'\1', name)
        
        names_saved = [FIND_NAME_REGEX.sub(r'\1', f) for f in saved]

        if name not in names_saved:
            raise FileNotFoundError(f'No chat with name {name} found.')
        
        idx = names_saved.index(name)
        
        return os.path.join(def_dir, 'chatgpt', saved[idx]), names_saved[idx]

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
    
    def _on_chat_create(self, inst: ChatGPT) -> None:
        """Handler for on_chat_create. Updates the internal dict with the new chat instance."""
        self._current = hash(inst)
        self._instances[hash(inst)] = {
            'name': '',
            'alias': inst.alias,
            'inst': weakref.proxy(inst),
        }
    
    def _on_chat_destroy(self, inst_hash: int) -> None:
        """Handler for on_chat_destroy. Removes the chat instance from the internal dict."""
        if inst_hash in self._instances:
            del self._instances[inst_hash]
        
        if inst_hash == self._current:
            self._current = None
    
    def _on_chat_used(self, inst_hash: int) -> None:
        """Handler for on_chat_used. Updates the current chat instance."""
        self._current = inst_hash