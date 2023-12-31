import pytest
from argparse import Namespace

from xontrib_chatgpt.args import _gpt_parse


@pytest.fixture(scope="module")
def argparse():
    return _gpt_parse()


@pytest.fixture
def default_namespace_dict():
    return {
        "cmd": "send",
        "text": [],
        "mode": "color",
        "type": "text",
        "name": "",
        "path": "",
        "n": 10,
    }


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ("something else", {"cmd": "send", "text": ["something", "else"]}),
        ("-p", {"cmd": "print", "text": []}),
        ("-s", {"cmd": "save", "text": []}),
        ("-P path", {"cmd": "send", "text": [], "path": "path"}),
        ("-P path -s", {"cmd": "save", "text": [], "path": "path"}),
        (
            "-P path -s --name name",
            {"cmd": "save", "text": [], "path": "path", "name": "name"},
        ),
        (
            "-P path -s --name name -m json",
            {"cmd": "save", "text": [], "path": "path", "name": "name", "mode": "json"},
        ),
        (
            "-P path -s --name name -m no-color -n 5",
            {
                "cmd": "save",
                "text": [],
                "path": "path",
                "name": "name",
                "mode": "no-color",
                "n": 5,
            },
        ),
        (
            "-P path -s --name name -m color -n 10 something else",
            {
                "cmd": "save",
                "text": ["something", "else"],
                "path": "path",
                "name": "name",
                "mode": "color",
                "n": 10,
            },
        ),
        (
            "-P path -s --name name -m color -t json",
            {
                "cmd": "save",
                "text": [],
                "path": "path",
                "name": "name",
                "mode": "color",
                "type": "json",
            },
        ),
        (
            "-P path -p --name name -m color -t json something else",
            {
                "cmd": "print",
                "text": ["something", "else"],
                "path": "path",
                "name": "name",
                "mode": "color",
                "type": "json",
            },
        ),
        (
            "-P path -p --name name -m color -t text -n 5 something else",
            {
                "cmd": "print",
                "text": ["something", "else"],
                "path": "path",
                "name": "name",
                "mode": "color",
                "type": "text",
                "n": 5,
            },
        ),
    ],
)
def test_parse_args(xession, argparse, args, expected, default_namespace_dict):
    new_dict = {**default_namespace_dict, **expected}
    expected = Namespace(**new_dict)
    assert argparse.parse_args(args.split()) == expected
