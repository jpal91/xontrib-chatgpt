"""Main ChatGPT class"""

import sys
import os
import json
import weakref
from typing import TextIO
from xonsh.built_ins import XSH
from xonsh.tools import indent
from xonsh.contexts import Block
from xonsh.lazyasd import LazyObject
from xonsh.ansi_colors import ansi_partial_color_format
from openai import OpenAIError, OpenAI

from xontrib_chatgpt.args import _gpt_parse
from xontrib_chatgpt.lazyobjs import (
    _openai,
)
from xontrib_chatgpt.utils import (
    get_token_list,
    parse_convo,
    print_res,
    format_markdown,
    get_default_path,
)
from xontrib_chatgpt.exceptions import (
    UnsupportedModelError,
    NoConversationsError,
    InvalidConversationsTypeError,
)

openai: OpenAI = LazyObject(_openai, globals(), "openai")  # type: ignore
parse = LazyObject(_gpt_parse, globals(), "parse")

DOCSTRING = """\
Allows for communication with ChatGPT from the xonsh shell.

This class can be assigned to a variable and used to have a continuous
    conversation with ChatGPT.
Alternatively, an alias 'chatgpt' is automatically registered 
    when the xontrib is loaded, which can be used to have one-off conversations.

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
    # Instance related help / docstrings / src
    >>> gpt?
    >>> gpt.print_convo?
    # CLI/Alias related help
    >>> gpt -h
    >>> chatgpt -h

Methods:
    print_convo - Prints the current conversation to the shell
    save_convo - Saves the current conversation to a file

Envs:
    $OPENAI_API_KEY - OpenAI API Key (REQUIRED)
    $OPENAI_CHAT_MODEL - OpenAI Chat Model
        Default: gpt-3.5-turbo
        Supported: gpt-3.5-turbo, gpt-4

Default Commands/Aliases:
    chatgpt - Alias for ChatGPT.fromcli
    chatgpt? - Alias for xonsh help ChatGPT
    chatgpt -h - Command for CLI help

"""


class ChatGPT(Block):
    """Allows for communication with ChatGPT from the xonsh shell"""

    __xonsh_block__ = str

    def __init__(self, alias: str = "", managed: bool = False) -> None:
        """
        Initializes the ChatGPT instance

        Parameters
        ----------
        alias : str, optional
            Alias to use for the instance. Defaults to ''.
            Will automatically register a xonsh alias under XSH.aliases[alias] if provided.
        """

        self.alias = alias
        self._base: list[dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "system",
                "content": "If your responses include code, make sure to wrap it in a markdown code block with the appropriate language.\nExample:\n```python\nprint('Hello World!')\n```",
            },
        ]
        self.messages: list[dict[str, str]] = []
        self._base_tokens: int = 53
        self._tokens: list = []
        self._max_tokens = 3000
        self.chat_idx = 0
        self._managed = managed

        if self.alias:
            # Make sure the __del__ method is called despite the alias pointing to the instance
            ref = weakref.proxy(self)
            XSH.aliases[self.alias] = lambda args, stdin=None: ref(args, stdin)

        if managed:
            XSH.builtins.events.on_chat_create.fire(inst=self)

    def __enter__(self):
        res = self.chat(self.macro_block.strip())
        print_res(res)
        return self

    def __exit__(self, *_):
        del self.macro_block

    def __call__(self, args: list[str], stdin: TextIO = None):
        if self._managed:
            XSH.builtins.events.on_chat_used.fire(inst=self)

        if args:
            pargs = parse.parse_args(args)
        elif stdin:
            pargs = parse.parse_args(stdin.read().strip().split())
        else:
            return

        if pargs.cmd == "send":
            res = self.chat(" ".join(pargs.text))
            print_res(res)
        elif pargs.cmd == "print":
            self.print_convo(pargs.n, pargs.mode)
        elif pargs.cmd == "save":
            self.save_convo(pargs.path, pargs.name, pargs.type)

    def __del__(self):
        if self.alias and self.alias in XSH.aliases:
            print(f"Deleting {self.alias}")
            del XSH.aliases[self.alias]

        if self._managed:
            XSH.builtins.events.on_chat_destroy.fire(inst=self)

    def __str__(self):
        stats = self._stats()
        return "\n".join([f"{k} {v}" for k, v, _, _ in stats])

    def __repr__(self):
        return f"ChatGPT(alias={self.alias or None})"

    @property
    def tokens(self) -> int:
        """Current convo tokens"""
        return self._base_tokens + sum(self._tokens[self.chat_idx :])

    @property
    def base(self) -> list[dict[str, str]]:
        return self._base

    @base.setter
    def base(self, msgs: list[dict[str, str]]) -> None:
        self._base_tokens = sum(get_token_list(msgs))
        self._base = msgs

    @property
    def chat_convo(self) -> list[dict[str, str]]:
        return self.base + self.messages[self.chat_idx :]

    def stats(self) -> None:
        """Prints conversation stats to shell"""
        stats = self._stats()
        return "\n".join(
            [
                ansi_partial_color_format(
                    "{} {}{}{} {}".format(tok, col, key, "{BOLD_WHITE}", val)
                )
                for key, val, col, tok in stats
            ]
        )

    def _stats(self) -> str:
        """Helper for stats and __str__"""
        stats = [
            ("Alias:", f"{self.alias or None}", "{BOLD_GREEN}", "🤖"),
            ("Tokens:", self.tokens, "{BOLD_BLUE}", "🪙"),
            ("Trim After:", f"{self._max_tokens} Tokens", "{BOLD_BLUE}", "🔪"),
            ("Messages:", len(self.messages), "{BOLD_BLUE}", "📨"),
        ]
        return stats

    def chat(self, text: str) -> str:
        """
        Main chat function for interfacing with OpenAI API

        This method is not meant to be called directly as calling the
            instance will call this method and print to the cli.
        However, it is avaliable and can be useful for assigning
            the response to a variable.

        Parameters
        ----------
        text : str
            Text to send to ChatGPT

        Returns
        -------
        str: Response from ChatGPT

        """

        model = XSH.env.get("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")
        choices = ["gpt-3.5-turbo", "gpt-4"]
        if model not in choices:
            raise UnsupportedModelError(
                f"Unsupported model: {model} - options are {choices}"
            )

        self.messages.append({"role": "user", "content": text})
        self.chat_idx -= 1

        try:
            response = openai.chat.completions.create(
                model=model,
                messages=self.chat_convo,
            )
            assert response, "Response is None"
        except OpenAIError as e:
            self.messages.pop()
            self.chat_idx += 1
            sys.exit(
                ansi_partial_color_format(
                    "{}OpenAI Error{}: {}".format("{BOLD_RED}", "{RESET}", e)
                )
            )

        res_text = dict(response.choices[0].message)
        assert res_text, "Response is empty"
        usage = response.usage
        assert usage, "Usage is None"
        user_toks, gpt_toks = (
            usage.prompt_tokens,
            usage.completion_tokens,
        )

        self.messages.append(res_text)
        self._tokens.extend([user_toks, gpt_toks])

        self.chat_idx -= 1
        self.trim_convo()

        return res_text["content"]

    def trim_convo(self) -> None:
        while self.chat_idx < -1 and self.tokens > self._max_tokens:
            self.chat_idx += 1

    def _get_json_convo(self, n: int) -> list[dict[str, str]]:
        """Returns the current conversation as a JSON string, up to n last items"""
        n = -n if n != 0 else 0
        messages = self.base + self.messages if n == 0 else self.messages[n:]

        return json.dumps(messages, indent=4)

    def _get_printed_convo(self, n: int, color: bool = True) -> list[tuple[str, str]]:
        """Helper method to get up to n items of conversation, formatted for printing"""
        user = XSH.env.get("USER", "user")
        convo = []
        n = -n if n != 0 else 0
        messages = self.base + self.messages if n == 0 else self.messages[n:]

        for msg in messages:
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
            elif msg["role"] == "system":
                role = (
                    ansi_partial_color_format("{BOLD_BLUE}" + "System:" + "{RESET}")
                    if color
                    else "System:"
                )
            else:
                continue

            if color:
                content = format_markdown(msg["content"])
            else:
                content = msg["content"]

            convo.append((role, indent(content)))

        return convo

    def print_convo(self, n: int = 10, mode: str = "color") -> str:
        """Prints the current conversation to shell, up to n last items, in the specified mode

        Parameters
        ----------
        n : int, optional
            Number of messages to print. Defaults to 10.
            If n is 0, the entire conversation will be printed.
        mode : str, optional
            Mode to print the conversation in. Defaults to 'color'.
            Options - 'color', 'no-color', 'json'

        Examples
        --------
            >>> chatgpt.print_convo(5, 'color') # prints the last 5 items of the conversation, with color
            >>> chatgpt.print_convo(0, 'json') # prints the entire conversation as a JSON string
            >>> chatgpt.print_convo(mode='no-color') # prints the last 10 items of the conversation,
                    without color or pygments markdown formatting
        """

        rtn_str = "\n"

        if not self.messages:
            raise NoConversationsError()

        if mode in ["color", "no-color"]:
            convo = self._get_printed_convo(n, mode == "color")
            for role, content in convo:
                rtn_str += role + "\n"
                rtn_str += content + "\n"
        elif mode == "json":
            convo = self._get_json_convo(n)
            rtn_str += convo
        else:
            raise InvalidConversationsTypeError(
                f'Invalid mode: "{mode}" -- options are "color", "no-color", and "json"'
            )
        print(rtn_str)

    def save_convo(
        self, path: str = "", name: str = "", mode: str = "text", override: bool = False
    ) -> None:
        """
        Saves conversation to path or default xonsh data directory

        Parameters
        ----------
        path : str, optional
            File path to save the conversation. Defaults to ''.
            If path is not specified, the conversation will be saved to the
            default xonsh data directory.
        name : str, optional
            Name of the conversation file. Defaults to ''.
            Ignored when path is specified.
        mode : str, optional
            Type of the conversation file. Defaults to 'text'.
            Options - 'text', 'json'
        override : bool, optional
            Whether or not to override existing files. Defaults to False.

        Returns
        -------
        None

        Notes
        -----
        Default File Path Structure:
            $XONSH_DATA_DIR/chatgpt/$USER_[name|alias|'chatgpt']_[date]_[index].[text|json]
        """
        if not self.messages:
            raise NoConversationsError()

        if not path:
            path = get_default_path(
                name=name, json_mode=mode == "json", override=override, alias=self.alias
            )
        elif os.path.exists(path) and not override:
            res = input(f"File already exists: {path}\nOverride? [Y/n]: ")

            if res.lower() == "n":
                return

        if mode == "text":
            convo = self._get_printed_convo(0, color=False)
        elif mode == "json":
            convo = self._get_json_convo(0)
        else:
            raise InvalidConversationsTypeError(
                f'Invalid mode: "{mode}" -- options are "text", and "json"'
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
        """Helper method for one off conversations from the shell.
        Conversation will not save to instance, and will not be saved to history.
        Not meant to be called directly, but from a xonsh alias.
        Alias 'chatgpt' is automatically registered when the xontrib is loaded.

        Parameters
        ----------
        args : list[str]
            Arguments passed from the shell
        stdin : TextIO, optional
            Text from stdin, by default None

        Usage
        -----
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

    @classmethod
    def fromconvo(cls, path, alias: str = "", managed: bool = False) -> "ChatGPT":
        """Loads a conversation from a saved file and returns new instance

        Parameters
        ----------
        path : str
            Path to the conversation file
        alias : str, optional
            Alias to use for the instance. Defaults to ''.
        managed : bool, optional
            Whether or not to register the instance with the chat manager.
            Defaults to False.

        Returns
        -------
        ChatGPT
            New instance with the loaded conversation
        """
        if not os.path.exists(path):
            bname = os.path.basename(path)
            default_dir = XSH.env.get(
                "XONSH_DATA_DIR",
                os.path.join(os.path.expanduser("~"), ".local", "share", "xonsh"),
            )
            guess_name = os.path.join(default_dir, "chatgpt", bname)

            if not os.path.exists(guess_name):
                raise FileNotFoundError(f"File not found: {path}")
            else:
                path = guess_name

        with open(path, "r") as f:
            convo = f.read()

        messages, base = parse_convo(convo)
        new_cls = cls(alias=alias, managed=managed)
        new_cls.messages = messages
        if base:
            new_cls.base = base
            new_cls._base_tokens = sum(get_token_list(base))
        new_cls._tokens = get_token_list(messages)
        new_cls.chat_idx = -len(messages)
        new_cls.trim_convo()

        return new_cls
