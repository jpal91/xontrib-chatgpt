"""Main ChatGPT class"""
import os
import json
import weakref
from datetime import datetime
from typing import TextIO
from xonsh.built_ins import XSH
from xonsh.tools import print_color, indent
from xonsh.contexts import Block
from xonsh.lazyasd import LazyObject
from xonsh.ansi_colors import ansi_partial_color_format

from xontrib_chatgpt.lazyobjs import(
    _openai,
    _MULTI_LINE_CODE,
    _SINGLE_LINE_CODE,
    _PYGMENTS,
    _markdown,
)
from xontrib_chatgpt.exceptions import (
    NoApiKeyError,
    UnsupportedModelError,
    NoConversationsError,
    InvalidConversationsTypeError,
)

openai = LazyObject(_openai, globals(), "openai")
MULTI_LINE_CODE = LazyObject(_MULTI_LINE_CODE, globals(), "MULTI_LINE_CODE")
SINGLE_LINE_CODE = LazyObject(_SINGLE_LINE_CODE, globals(), "SINGLE_LINE_CODE")
PYGMENTS = LazyObject(_PYGMENTS, globals(), "PYGMENTS")
markdown = LazyObject(_markdown, globals(), "markdown")

DOCSTRING = """\
Allows for communication with ChatGPT from the xonsh shell.

This class can be assigned to a variable and used to have a continuous
    conversation with ChatGPT.
Alternatively, an alias 'chatgpt' is automatically registered 
    when the xontrib is loaded, which can be used to have one off conversations.

Args:
    alias (str, optional): Alias to use for the instance. Defaults to ''.

Usage:
    # With the pre-registered 'chatgpt' alias
    >>> chatgpt [text] # text will be sent to ChatGPT
    >>> echo [text] | chatgpt # text from stdin will be sent to ChatGPT

    # With a ChatGPT instance and context manager
    >>> gpt = ChatGPT()
    >>> with! gpt:
            [text] # text will be sent to ChatGPT
    
    # With a ChatGPT instance and an alias
    >>> gpt = ChatGPT('gpt')
    >>> gpt [text] # text will be sent to ChatGPT
    >>> with! gpt:
            [text] # text will be sent to ChatGPT
    
    # Get Help
    >>> chatgpt? # With default alias
    >>> gpt = ChatGPT()
    >>> gpt?
    >>> gpt.print_convo?

Methods:
    print_convo - Prints the current conversation to the shell
    save_convo - Saves the current conversation to a file

Envs:
    $OPENAI_API_KEY - OpenAI API Key (REQUIRED)
    $OPENAI_CHAT_MODEL - OpenAI Chat Model
        Default: gpt-3.5-turbo
        Supported: gpt-3.5-turbo, gpt-4

"""


class ChatGPT(Block):
    """Allows for communication with ChatGPT from the xonsh shell"""

    __xonsh_block__ = str

    def __init__(self, alias: str = "") -> None:
        """
        Initializes the ChatGPT instance

        Args:
            alias (str, optional): Alias to use for the instance. Defaults to ''.
                Will automatically register a xonsh alias under XSH.aliases[alias] if provided.
        """

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
        self._print_res(res)
        return self

    def __exit__(self, *_):
        del self.macro_block

    def __call__(self, args: list[str], stdin: TextIO = None):
        if args:
            res = self.chat(" ".join(args))
        elif stdin:
            res = self.chat(stdin.read().strip())
        else:
            return

        self._print_res(res)

    def __del__(self):
        if self.alias and self.alias in XSH.aliases:
            print(f"Deleting {self.alias}")
            del XSH.aliases[self.alias]

    def __str__(self):
        stats = self._stats()
        return "\n".join([f"{k} {v}" for k, v, _ in stats])

    def __repr__(self):
        return f"ChatGPT(alias={self.alias or None})"

    @property
    def tokens(self) -> int:
        """Current convo tokens"""
        return sum(self._tokens)

    @property
    def stats(self) -> None:
        """Prints conversation stats to shell"""
        stats = self._stats()
        for k, v, c in stats:
            print_color("{}{}{} {}".format(c, k, "{BOLD_WHITE}", v))

    def _stats(self) -> str:
        """Helper for stats and __str__"""
        stats = [
            ("Alias:", f"{self.alias or None}", "{BOLD_YELLOW}"),
            ("Tokens:", self.tokens, "{BOLD_GREEN}"),
            ("Trim After:", f"{self._max_tokens} Tokens", "{BOLD_BLUE}"),
            ("Mode:", XSH.env.get("OPENAI_CHAT_MODEL", "gpt-3.5-turbo"), "{BOLD_BLUE}"),
            ("Messages:", len(self.messages), "{BOLD_BLUE}"),
        ]
        return stats

    def chat(self, text: str) -> str:
        """
        Main chat function for interfacing with OpenAI API
        
        This method is not meant to be called directly as calling the 
            instance will call this method and print to the cli.
        However, it is avaliable and can be useful for assigning 
            the response to a variable.
        
        Args:
            text (str): Text to send to ChatGPT
        
        Returns:
            str: Response from ChatGPT

        """

        model = XSH.env.get("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")
        choices = ["gpt-3.5-turbo", "gpt-4"]
        if model not in choices:
            raise UnsupportedModelError(
                f"Unsupported model: {model} - options are {choices}"
            )

        if not openai.api_key:
            api_key = XSH.env.get("OPENAI_API_KEY", None)
            if not api_key:
                raise NoApiKeyError()
            openai.api_key = api_key

        self.messages.append({"role": "user", "content": text})

        response = openai.ChatCompletion.create(
            model=model,
            messages=self.base + self.messages,
        )

        res_text = response["choices"][0]["message"]
        tokens = response["usage"]["total_tokens"]

        self.messages.append(res_text)
        self._tokens.append(tokens)

        if self.tokens >= self._max_tokens:
            self._trim()

        return res_text["content"]

    def _trim(self) -> None:
        """Trims conversation to make sure it doesn't exceed the max tokens"""
        tokens = self.tokens
        while tokens > self._max_tokens:
            self.messages.pop(0)
            tokens -= self._tokens.pop(0)

    def _print_res(self, res: str) -> None:
        """Called after receiving response from ChatGPT, prints the response to the shell"""
        res = self._format_markdown(res)
        res = indent(res)
        print(ansi_partial_color_format("\n{BOLD_BLUE}ChatGPT:{RESET}\n"))
        print(res)

    def _format_markdown(self, text: str) -> str:
        """Formats the text using the Pygments Markdown Lexer, removes markdown code '`'s"""
        text = markdown(text)
        text = MULTI_LINE_CODE.sub("", text)
        text = SINGLE_LINE_CODE.sub(r"\1", text)
        return text

    def _get_json_convo(self, n: int) -> list[dict[str, str]]:
        """Returns the current conversation as a JSON string, up to n last items"""
        n = -n if n != 0 else 0
        return json.dumps(self.messages[n:], indent=4)

    def _get_printed_convo(self, n: int, color: bool = True) -> list[tuple[str, str]]:
        """Helper method to get up to n items of conversation, formatted for printing"""
        user = XSH.env.get("USER", "user")
        convo = []
        n = -n if n != 0 else 0

        for msg in self.messages[n:]:
            if msg["role"] == "user":
                role = (
                    ansi_partial_color_format("{BOLD_GREEN}" + f"{user}:" + "{RESET}")
                    if color
                    else f"{user}:"
                )
            elif msg["role"] == "assistant":
                role = (
                    ansi_partial_color_format("{BOLD_BLUE}" + "ChatGPT:" + "{RESET}")
                    if color
                    else "ChatGPT:"
                )
            else:
                continue

            if color:
                content = self._format_markdown(msg["content"])
            else:
                content = msg["content"]

            convo.append((role, indent(content)))

        return convo

    def print_convo(self, n: int = 10, mode: str = "color") -> None:
        """Prints the current conversation to shell, up to n last items, in the specified mode

        Args:
            n (int, optional): Number of items to print, starting from the last response. Defaults to 10. 0 == all.
            mode (str, optional): Mode to print in. Defaults to 'color'. Options - 'color', 'no-color', 'json'

        Examples:
            >>> chatgpt.print_convo(5, 'color') # prints the last 5 items of the conversation, with color
            >>> chatgpt.print_convo(0, 'json') # prints the entire conversation as a JSON string
            >>> chatgpt.print_convo(mode='no-color') # prints the last 10 items of the conversation,
                    without color or pygments markdown formatting
        """

        print("")

        if not self.messages:
            raise NoConversationsError()

        if mode in ["color", "no-color"]:
            convo = self._get_printed_convo(n, mode == "color")
        elif mode == "json":
            convo = self._get_json_convo(n)
            print(convo)
            return
        else:
            raise InvalidConversationsTypeError(
                f'Invalid mode: "{mode}" -- options are "color", "no-color", and "json"'
            )

        for role, content in convo:
            print(role)
            print(content)

        return
    
    def _get_default_path(self, name: str = '', json_mode:bool=False) -> str:
        """Helper method to get the default path for saving conversations"""
        user = XSH.env.get("USER", "user")
        data_dir = XSH.env.get("XONSH_DATA_DIR", os.path.join(os.path.expanduser("~"), ".local", "share", "xonsh"))
        chat_dir = os.path.join(data_dir, "chatgpt")

        if not os.path.exists(chat_dir):
            os.makedirs(chat_dir)
        
        date, idx = datetime.now().strftime("%Y-%m-%d"), 1
        path_prefix, ext = os.path.join(chat_dir, f"{user}_{name or self.alias or 'chatgpt'}_{date}"), ".json" if json_mode else ".txt"
        
        if os.path.exists(f'{path_prefix}{ext}'):
            while os.path.exists(path_prefix + f"_{idx}{ext}"):
                idx += 1
            path = path_prefix + f"_{idx}{ext}"
        else:
            path = path_prefix + f"{ext}"
        
        return path

    def save_convo(self, path: str = '', name: str = '', mode: str = "no-color") -> None:
        """
        Saves conversation to path or default xonsh data directory
        
        Args:
            path (str, optional): Path to save conversation to. Defaults to ''.
            name (str, optional): Name to use in the filename. Defaults to ''.
            mode (str, optional): Mode to save in. Defaults to 'no-color'. Options - 'color', 'no-color', 'json'

            When path is specified, name will be ignored.
        
        Default File Path Structure:
            $XONSH_DATA_DIR/chatgpt/$USER_[name|alias|'chatgpt']_[date]_[index].[text|json]
        """
        if not self.messages:
            raise NoConversationsError()
        
        if not path:
            path = self._get_default_path(name=name, json_mode=mode == "json")

        if mode in ["color", "no-color"]:
            convo = self._get_printed_convo(0, mode == "color")
        elif mode == "json":
            convo = self._get_json_convo(0)
        else:
            raise InvalidConversationsTypeError(
                f'Invalid mode: "{mode}" -- options are "color", "no-color", and "json"'
            )

        with open(path, "w") as f:
            if mode == "json":
                f.write(convo)
            else:
                for role, content in convo:
                    f.write(role + "\n")
                    f.write(content + "\n")

        print("Conversation saved to: " + str(path))
        return

    @staticmethod
    def fromcli(args: list[str], stdin: TextIO = None) -> None:
        """\
        Helper method for one off conversations from the shell.
        Conversation will not save to instance, and will not be saved to history.
        Not meant to be called directly, but from a xonsh alias.
            Alias 'chatgpt' is automatically registered when the xontrib is loaded.

        Usage:
            >>> chatgpt [text] # text will be sent to ChatGPT
            >>> echo [text] | chatgpt # text from stdin will be sent to ChatGPT
            >>> cat [text file] | chatgpt # text from file will be sent to ChatGPT
        """
        inst = ChatGPT()
        inst(args, stdin)
        return None

    @staticmethod
    def getdoc() -> str:
        return DOCSTRING