import re
import json
import weakref
from collections import namedtuple
from dataclasses import dataclass
from textwrap import dedent
from typing import TextIO
from xonsh.built_ins import XSH, XonshSession
from xonsh.tools import print_color, indent
from xonsh.contexts import Block
from xonsh.lazyasd import lazyobject
from xonsh.ansi_colors import ansi_partial_color_format

__all__ = ()

@lazyobject
def openai():
    import openai
    return openai

@lazyobject
def CODE_BLOCK():
    return re.compile(r'```(.*?)\n(.*?)```', re.DOTALL)

@lazyobject
def MULTI_LINE_CODE():
    return re.compile(r'```.*?\n', re.DOTALL)

@lazyobject
def SINGLE_LINE_CODE():
    return re.compile(r'`(.*?)`')

@lazyobject
def PYGMENTS():
    """Lazy loading of pygments to avoid slowing down shell startup"""
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.lexers.python import PythonLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.styles.gh_dark import GhDarkStyle

    container = namedtuple('container', ['highlight', 'get_lexer_by_name', 'PythonLexer', 'Terminal256Formatter', 'GhDarkStyle'])
    return container(highlight, get_lexer_by_name, PythonLexer, Terminal256Formatter, GhDarkStyle)

@lazyobject
def markdown():
    from pygments import highlight
    from pygments.lexers.markup import MarkdownLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.styles.gh_dark import GhDarkStyle

    return lambda text: highlight(text, MarkdownLexer(), Terminal256Formatter(style=GhDarkStyle))

class NoApiKey(Exception):
    """Raised when no API key is found"""
    pass

class UnsupportedModel(Exception):
    """Raised when an unsupported model is used"""
    pass

@dataclass
class ChatEnv:
    """Helper class to improve efficiency in getting env variables"""

    OPENAI_CHAT_MODEL: str | None = XSH.env.get('OPENAI_CHAT_MODEL', 'gpt-3.5-turbo')
    OPENAI_API_KEY: str | None = XSH.env.get('OPENAI_API_KEY', None)

    def __contains__(self, key):
        return key in vars(self)

def env_handler(name: str, oldvalue: str, newvalue: str):
    """Env change event handler, updates local env state"""
    if name in chatenv:
        setattr(chatenv, name, newvalue)


class ChatGPT(Block):
    __xonsh_block__ = str
    
    def __init__(self, alias:str=''):
        self.alias = alias
        self.base: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        self.messages: list[dict[str, str]] = []
        self._tokens: list = []
        self._max_tokens = 3000

        if self.alias:
            # Make sure the __del__ method is called despite the alias pointing to the instance
            ref = weakref.proxy(self)
            XSH.aliases[self.alias] = lambda args, stdin=None: ref(args, stdin)

    def __enter__(self):
        res = self.chat(self.macro_block.strip())
        self.print_res(res)
        return self
    
    def __exit__(self, *_):
        del self.macro_block
    
    def __call__(self, args: list[str], stdin:TextIO=None):
        if args:
            res = self.chat(" ".join(args))
        elif stdin:
            res = self.chat(stdin.read().strip())
        else:
            return
        
        self.print_res(res)
    
    def __del__(self):
        if self.alias and self.alias in XSH.aliases:
            print(f'Deleting {self.alias}')
            del XSH.aliases[self.alias]
    
    @property
    def tokens(self):
        return sum(self._tokens)
    
    @property
    def stats(self):
        stats = f"""
        Tokens: {self.tokens}
        Trim After: {self._max_tokens} Tokens
        Mode: {chatenv.OPENAI_CHAT_MODEL}
        Messages: {len(self.messages)}
        """
        return print(dedent(stats))
    
    def chat(self, text):
        api_key = chatenv.OPENAI_API_KEY
        if not api_key:
            raise NoApiKey('No OpenAI API key found')
        
        model = chatenv.OPENAI_CHAT_MODEL
        if model not in ['gpt-3.5-turbo', 'gpt-4']:
            raise UnsupportedModel(f'Unsupported model: {model}')
        
        self.messages.append({"role": "user", "content": text})

        if not openai.api_key:
            openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model=model,
            messages=self.base + self.messages,
        )

        res_text = response['choices'][0].message
        tokens = response['usage']['total_tokens']

        self.messages.append(res_text)
        self._tokens.append(tokens)

        if self.tokens >= self._max_tokens:
            self.trim()

        return res_text['content']
    
    def trim(self):
        tokens = self.tokens
        while tokens > self._max_tokens:
            self.messages.pop(0)
            tokens -= self._tokens.pop(0)
    
    def handle_code_block(self, match: re.Match) -> str:
        """Matches any code block in the string, strips each of the leading/following "`"s, 
            and uses pygments to highlight
        """
        if match.group(1) and match.group(1) not in ['python', 'py']:
            lexer = PYGMENTS.get_lexer_by_name(match.group(1))
        else:
            lexer = PYGMENTS.PythonLexer()
        
        return PYGMENTS.highlight(match.group(2), lexer, PYGMENTS.Terminal256Formatter(style=PYGMENTS.GhDarkStyle))
        
    
    def print_res(self, res: str):        
        res = self._format_markdown(res)
        res = indent(res)
        print(ansi_partial_color_format('\n{BOLD_BLUE}ChatGPT:{RESET}\n'))
        print(res)
    
    def _format_markdown(self, text: str) -> str:
        text = markdown(text)
        text = MULTI_LINE_CODE.sub('', text)
        text = SINGLE_LINE_CODE.sub(r'\1', text)
        return text
    
    def _get_json_convo(self, n: int) -> list[dict[str, str]]:
        n = -n if n != 0 else 0
        return json.dumps(self.messages[n:], indent=4)

    def _get_printed_convo(self, n: int, color=True) -> list[tuple[str, str]]:
        user = XSH.env.get('USER', 'user')
        convo = []
        n = -n if n != 0 else 0
        
        for msg in self.messages[n:]:
            if msg['role'] == 'user':
                role = ansi_partial_color_format('{BOLD_GREEN}' + f'{user}:' + '{RESET}') if color else f'{user}:'
            elif msg['role'] == 'assistant':
                role = ansi_partial_color_format('{BOLD_BLUE}' + 'ChatGPT:' + '{RESET}') if color else 'ChatGPT:'
            else:
                continue

            if color:
                content = self._format_markdown(msg['content'])
            else:
                content = msg['content']
            
            convo.append((role, indent(content)))
        
        return convo

    def print_convo(self, n=10, mode='color'):
        print('')
        if mode in ['color', 'no-color']:
            convo = self._get_printed_convo(n, mode == 'color')
        elif mode == 'json':
            convo = self._get_json_convo(n)
            print(convo)
            return
        else:
            print_color('{BOLD_RED}Invalid mode: "' + mode + '"{RESET} -- options are "color", "no-color", and "json"')
            return
        
        for role, content in convo:
            print(role)
            print(content)
        
    
    def save_convo(self, path: str, mode='no-color'):
        if mode in ['color', 'no-color']:
            convo = self._get_printed_convo(0, mode == 'color')
        elif mode == 'json':
            convo = self._get_json_convo(0)
        else:
            print_color('{BOLD_RED}Invalid mode: "' + mode + '"{RESET} -- options are "color", "no-color", and "json"')
            return
        
        with open(path, 'w') as f:
            if mode == 'json':
                f.write(convo)
            else:
                for role, content in convo:
                    f.write(role + '\n')
                    f.write(content + '\n')
            
        print_color('{}Conversation saved to: {}{}{}'.format('{BOLD_GREEN}', '{BOLD_BLUE}', path, '{RESET}'))
                
    
    @staticmethod
    def fromcli(args: list[str], stdin:TextIO=None) -> None:
        inst = ChatGPT()
        inst(args, stdin)
        return None

chatenv = ChatEnv()
    
def _load_xontrib_(xsh: XonshSession, **_):
    xsh.aliases['chatgpt'] = lambda args, stdin=None: ChatGPT.fromcli(args, stdin)
    xsh.builtins.events.on_envvar_change(env_handler)

    return {'ChatGPT': ChatGPT}

def _unload_xontrib_(xsh: XonshSession, **_):
    del XSH.aliases['chatgpt']
    xsh.builtins.events.on_envvar_change.remove(env_handler)