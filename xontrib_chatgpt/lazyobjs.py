import re
from collections import namedtuple

#############
# Lazy Objects
#############

def _openai():
    """Imports openai"""
    import openai

    return openai

def _tiktoken():
    """Imports tiktoken"""
    import tiktoken

    return tiktoken.get_encoding('cl100k_base')

def _MULTI_LINE_CODE():
    """Regex to remove multiline code blocks (```code```) from markdown"""
    return re.compile(r"```.*?\n", re.DOTALL)

def _SINGLE_LINE_CODE():
    """Regex to remove single line code blocks (`code`) from markdown"""
    return re.compile(r"`(.*?)`")

# def _CHAT_REGEX():
#     """Regex to convert saved chats back into a list of messages"""
#     # return re.compile(r'\n?(.+?):\n(.+?)(?=\nChatGPT|$)', re.DOTALL)
#     return re.compile(r'^(.+):\n(\s{4}.*)+', re.MULTILINE | re.DOTALL)

# def _COLOR_REGEX():
#     """Regex to assist in striping all x1b ansi escape codes"""
#     return re.compile(r'\x1b.*?m', re.DOTALL)

def _PYGMENTS():
    """Lazy loading of pygments to avoid slowing down shell startup"""
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.lexers.python import PythonLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.styles.gh_dark import GhDarkStyle

    container = namedtuple(
        "container",
        [
            "highlight",
            "get_lexer_by_name",
            "PythonLexer",
            "Terminal256Formatter",
            "GhDarkStyle",
        ],
    )
    return container(
        highlight, get_lexer_by_name, PythonLexer, Terminal256Formatter, GhDarkStyle
    )

def _markdown():
    """Formats markdown text using pygments"""
    from pygments import highlight
    from pygments.lexers.markup import MarkdownLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.styles.gh_dark import GhDarkStyle

    return lambda text: highlight(
        text, MarkdownLexer(), Terminal256Formatter(style=GhDarkStyle)
    )