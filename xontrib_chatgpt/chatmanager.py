import os
import weakref
from collections import defaultdict
from typing import Optional, Union, TextIO
from argparse import ArgumentParser
from re import Pattern
from xonsh.built_ins import XSH
from xonsh.lazyasd import LazyObject
from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.lazyobjs import _FIND_NAME_REGEX
from xontrib_chatgpt.args import _cm_parse

FIND_NAME_REGEX: Pattern = LazyObject(_FIND_NAME_REGEX, globals(), 'FIND_NAME_REGEX')
PARSER: ArgumentParser = LazyObject(_cm_parse, globals(), 'PARSER')

class ChatManager:
    """Class to manage multiple chats"""

    def __init__(self):
        self._instances: dict[int, dict[str, Union[str, ChatGPT]]] = defaultdict(dict)
        self._current: Optional[int] = None
        self._update_inst_dict()

    def __call__(self, args: list[str], stdin: TextIO=None):
        if args:
            pargs = PARSER.parse_args(args)
        elif stdin:
            pargs = PARSER.parse_args(stdin.read().strip().split())
        else:
            return PARSER.print_help()
        
        if pargs.current:
            if self._current is None:
                return 'No active chat!'
            else:
                return str(self._instances[self._current]['inst'])
        
        if pargs.cmd == 'add':
            return self.add(pargs.name[0])
        elif pargs.cmd in ['list', 'ls']:
            return self.ls(saved=pargs.saved)
        elif pargs.cmd == 'load':
            return self.load(pargs.name[0])
        elif pargs.cmd == 'save':
            return self.save(chat_name=pargs.name, mode=pargs.mode)
        elif pargs.cmd == 'print':
            return self.print_chat(chat_name=pargs.name, n=pargs.n, mode=pargs.mode)
        elif pargs.cmd == 'help':
            return self.help(tgt=pargs.tgt)
        else:
            return PARSER.print_help()

    def add(self, chat_name: str) -> str:
        """Create new chat instance"""
        if chat_name in self.chat_names():
            return 'Chat with that name already exists!'
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
        
        curr_names = self.chat_names()
        
        if name in curr_names:
            idx = 0
            while name + str(idx) in curr_names:
                idx += 1
            print(f'Chat with name {name} already loaded. Updating to {name + str(idx)}')
            name += str(idx)
            
        inst = ChatGPT.fromconvo(path, alias=name, managed=True)
        XSH.ctx[name] = inst
        self._instances[hash(inst)]['name'] = name

        return f'Loaded chat {name} from {path}'

    def save(self, chat_name: str = '', mode: str = 'text') -> Optional[str]:
        if not chat_name and not self._current:
            return 'No active chat!'
        elif not chat_name:
            chat = self._instances[self._current]
        else:
            try:
                chat = self._instances[hash(XSH.ctx[chat_name])]
            except KeyError:
                return f'No chat with name {chat_name} found.'

        return chat['inst'].save_convo(mode=mode)


    def print_chat(self, chat_name: str = '', n: int = 10, mode: str = 'color') -> Optional[str]:
        if not chat_name and not self._current:
            return 'No active chat!'
        elif not chat_name:
            chat = self._instances[self._current]
        else:
            try:
                chat = self._instances[hash(XSH.ctx[chat_name])]
            except KeyError:
                return f'No chat with name {chat_name} found.'
        
        chat['inst'].print_convo(n=n, mode=mode)

    def help(self, tgt: str = '') -> None:
        if not tgt:
            PARSER.print_help()
            return
        
        if hasattr(self, tgt):
            XSH.help(getattr(self, tgt))
        elif hasattr(ChatGPT, tgt):
            XSH.help(getattr(ChatGPT, tgt))
        else:
            PARSER.print_help()

    def chat_names(self) -> list[str]:
        return [inst['name'] for inst in self._instances.values()]

    def _find_saved(self) -> list[str]:
        def_dir = os.path.join(XSH.env['XONSH_DATA_DIR'], 'chatgpt')
        return [f for f in os.listdir(def_dir) if os.path.isfile(os.path.join(def_dir, f))]
    
    def _find_path_from_name(self, name: str) -> tuple[str, str]:
        def_dir = XSH.env['XONSH_DATA_DIR']
        saved = self._find_saved()

        if name in saved:
            return os.path.join(def_dir, 'chatgpt', name), FIND_NAME_REGEX.sub(r'\1', name)
        
        names_saved = [
            (n, f) for n, f in
            [(FIND_NAME_REGEX.sub(r'\1', f), f) for f in saved]
            if n == name
        ]

        if not names_saved:
            raise FileNotFoundError(f'No chat with name {name} found.')
        elif len(names_saved) > 1:
            chat_name, file = self._choose_from_multiple(names_saved)
        else:
            chat_name, file = names_saved[0]
        
        
        return os.path.join(def_dir, 'chatgpt', file), chat_name
    
    def _choose_from_multiple(self, chats: list[tuple[str, str]]) -> tuple[str, str]:
        print('Multiple choices found, please choose from:')
        [print(f'  {i + 1}. {n[0]}') for i, n in enumerate(chats)]
        
        while True:
            max_choice = len(chats)
            choice = input(f'Number (1 - {max_choice}): ')

            try:
                choice = int(choice)
            except ValueError:
                print('Invalid input, please enter a number.')
                continue

            if not 0 < choice <= max_choice:
                print(f'Invalid input, please enter a number between 1 and {max_choice}.')
                continue

            return chats[choice - 1]

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