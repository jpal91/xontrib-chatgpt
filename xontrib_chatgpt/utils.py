"""Utility Functions for xontrib-chatgpt"""

import os
import json
from typing import Union
from datetime import datetime
from textwrap import dedent

from xonsh.built_ins import XSH
from xonsh.tools import indent
from xonsh.ansi_colors import ansi_partial_color_format
from xonsh.lazyasd import LazyObject

from xontrib_chatgpt.lazyobjs import (
    _tiktoken,
    _MULTI_LINE_CODE,
    _SINGLE_LINE_CODE,
    _markdown,
    _YAML,
)
from xontrib_chatgpt.exceptions import MalformedSysMsgError


tiktoken = LazyObject(_tiktoken, globals(), "tiktoken")
MULTI_LINE_CODE = LazyObject(_MULTI_LINE_CODE, globals(), "MULTI_LINE_CODE")
SINGLE_LINE_CODE = LazyObject(_SINGLE_LINE_CODE, globals(), "SINGLE_LINE_CODE")
markdown = LazyObject(_markdown, globals(), "markdown")
YAML = LazyObject(_YAML, globals(), "YAML")


def parse_convo(convo: str) -> tuple[list[dict[str, str]]]:
    """Parses a conversation from a saved file

    Parameters
    ----------
    convo : str
        Conversation to parse

    Returns
    -------
    tuple[list[dict[str, str]]]
        Parsed conversation and base system messages
    """
    try:
        convo = json.loads(convo)
    except json.JSONDecodeError:
        pass
    else:
        base, messages = [], []
        for msg in convo:
            if msg["role"] == "system":
                base.append(msg)
            else:
                messages.append(msg)
        return messages, base

    convo = convo.split("\n")
    messages, base, user, idx, n = [], [], True, 0, len(convo)

    # Couldn't figure out how to do this with regex, so while loop instead
    while idx < n:
        if not convo[idx]:
            idx += 1
            continue

        if convo[idx].startswith("System"):
            msg = {"role": "system", "content": ""}
        else:
            msg = {"role": "user" if user else "assistant", "content": ""}

        idx += 1

        if idx >= n:
            break

        while idx < n and convo[idx].startswith(" "):
            msg["content"] += convo[idx] + "\n"
            idx += 1

        msg["content"] = dedent(msg["content"])

        if msg["role"] == "system":
            base.append(msg)
        else:
            messages.append(msg)
            user = not user

    return messages, base


def get_token_list(messages: list[dict[str, str]]) -> list[int]:
    """Gets the chat tokens for the loaded conversation

    Parameters
    ----------
    messages : list[dict[str, str]]
        Messages from the conversation

    Returns
    -------
    list[int]
        List of tokens for each message
    """
    tokens_per_message = 3
    tokens = [3]

    for message in messages:
        num_tokens = 0
        num_tokens += tokens_per_message
        for v in message.values():
            num_tokens += len(tiktoken.encode(v))
        tokens.append(num_tokens)

    return tokens


def print_res(res: str) -> None:
    """Called after receiving response from ChatGPT, prints the response to the shell"""
    res = format_markdown(res)
    res = indent(res)
    print(ansi_partial_color_format("\n{BOLD_BLUE}ChatGPT:{RESET}\n"))
    print(res)


def format_markdown(text: str) -> str:
    """Formats the text using the Pygments Markdown Lexer, removes markdown code '`'s"""
    text = markdown(text)
    text = MULTI_LINE_CODE.sub("", text)
    text = SINGLE_LINE_CODE.sub(r"\1", text)
    return text


def get_default_path(
    name: str = "", json_mode: bool = False, override: bool = False, alias: str = ""
) -> str:
    """Helper method to get the default path for saving conversations"""
    user = XSH.env.get("USER", "user")
    data_dir = XSH.env.get(
        "XONSH_DATA_DIR",
        os.path.join(os.path.expanduser("~"), ".local", "share", "xonsh"),
    )
    chat_dir = os.path.join(data_dir, "chatgpt")

    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)

    date, idx = datetime.now().strftime("%Y-%m-%d"), 1
    path_prefix, ext = (
        os.path.join(chat_dir, f"{user}_{name or alias or 'chatgpt'}_{date}"),
        ".json" if json_mode else ".txt",
    )

    if os.path.exists(f"{path_prefix}{ext}") and not override:
        while os.path.exists(path_prefix + f"_{idx}{ext}"):
            idx += 1
        path = path_prefix + f"_{idx}{ext}"
    else:
        path = path_prefix + f"{ext}"

    return path


def convert_to_sys(msgs: Union[str, dict, list]) -> list[dict]:
    """Returns a list of dicts from a string of python dict, json, or yaml.
    Calls itself recursively until the result is either a list[dict]
    or raises an error.

    Will attempt to parse yaml only if package is installed.

    Parameters
    ----------
    msgs : Union[str, dict, list]
        Messages to convert to system messages

    Returns
    -------
    list[dict]

    Raises
    ------
    MalformedSysMsgError
        Raised when the messages are not properly formatted

    Examples
    --------
    msgs :
        '[{"role": "system", "content": "Hello"}, {"role": "system", "content": "Hi there!"}]'
        '{"role": "system", "content": "Hello"}'
        '- role: system\n  content: Hello\n- role: system\n  content: Hi there!'
    """

    if isinstance(msgs, str):
        msgs = msgs.strip()
        try:
            msgs = eval(msgs)
        except SyntaxError:
            pass

    if isinstance(msgs, dict):
        return convert_to_sys([msgs])
    elif isinstance(msgs, list):
        for m in msgs:
            if "content" not in m:
                raise MalformedSysMsgError(msgs)
            m["role"] = "system"
        return msgs
    elif YAML is not None:
        try:
            return YAML.safe_load(msgs)
        except YAML.YAMLError:
            pass

    raise MalformedSysMsgError(msgs)
