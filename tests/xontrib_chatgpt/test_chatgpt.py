import io
import json
import shutil
import pytest
from datetime import datetime
from openai.error import RateLimitError
from xontrib_chatgpt.chatgpt import ChatGPT, parse_convo, get_token_list
from xontrib_chatgpt.exceptions import (
    NoApiKeyError,
    UnsupportedModelError,
    NoConversationsError,
    InvalidConversationsTypeError,
)


MARKDOWN_BLOCK = """\
Hello!
```python
print('Hello World!')
```
"""

MARKDOWN_BLOCK_2 = """\
Sure here is a `Hello world` function:
```python
def hello_world():
    print('Hello world!')
```
"""


class DummyAI:
    def __init__(self):
        self.api_key = None

    def create(self, **_):
        return {
            "choices": [{"message": {"content": "test", "role": "assistant"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


@pytest.fixture(scope="module")
def temp_home(tmpdir_factory):
    home = tmpdir_factory.mktemp("home")
    home.mkdir("expected")
    home.mkdir("saved")
    data_dir = home.mkdir("data_dir")
    data_dir.mkdir("chatgpt")
    fixtures = [
        "color_convo.txt",
        "no_color_convo.txt",
        "no_color_convo2.txt",
        "convo.json",
        "convo2.json",
        "long_convo.txt",
    ]
    for f in fixtures:
        shutil.copy(f"tests/fixtures/{f}", f"{home}/expected/{f}")
    shutil.copy(
        f"tests/fixtures/no_color_convo.txt", f"{data_dir}/chatgpt/no_color_convo.txt"
    )
    yield home


@pytest.fixture
def monkeypatch_openai(monkeypatch):
    dummy_ai = DummyAI()
    dummy_ai.ChatCompletion = DummyAI()
    monkeypatch.setattr("xontrib_chatgpt.chatgpt.openai", dummy_ai)


@pytest.fixture
def chat(xession):
    return ChatGPT()


@pytest.fixture
def chat_w_alias(xession):
    chat = ChatGPT("gpt")
    yield chat
    del chat


def test_it_loads(load_xontrib, xession):
    load_xontrib("chatgpt")
    assert "chatgpt" in xession.aliases


def test_alias_creation(xession):
    assert "chat" not in xession.aliases
    chat = ChatGPT()
    assert "chat" not in xession.aliases
    chat = ChatGPT("chat")
    assert "chat" in xession.aliases
    del xession.aliases["chat"]


def test_defualt_attribs(xession, chat):
    assert chat.messages == []
    assert chat._tokens == []
    assert chat._max_tokens == 3000
    assert chat.alias == ""
    assert chat.tokens == 53


def test_tokens(xession, chat):
    chat._tokens = [1, 2, 3]
    assert chat.tokens == 59


def test_chat_raises_error_with_no_api_key(xession, chat, monkeypatch_openai):
    xession.env["OPENAI_API_KEY"] = ""
    with pytest.raises(NoApiKeyError):
        chat.chat("test")


def test_chat_raises_error_with_no_chat_model(xession, chat, monkeypatch_openai):
    xession.env["OPENAI_API_KEY"] = "test"
    xession.env["OPENAI_CHAT_MODEL"] = "test"
    with pytest.raises(UnsupportedModelError):
        chat.chat("test")


def test_chat_catches_openai_errors(xession, chat, monkeypatch):
    xession.env["OPENAI_API_KEY"] = "test"
    xession.env["OPENAI_CHAT_MODEL"] = "gpt-3.5-turbo"

    def raise_it(*_, **__):
        raise RateLimitError("test")

    monkeypatch.setattr(
        "xontrib_chatgpt.chatgpt.openai.ChatCompletion.create", raise_it
    )
    with pytest.raises(SystemExit):
        chat.chat("test")


def test_chat_convo(xession, chat):
    assert chat.chat_convo == chat.base
    chat.messages = [
        {"role": "user", "content": "test"},
        {"role": "assistant", "content": "test"},
    ]
    chat.chat_idx -= 2
    assert chat.chat_convo == chat.base + chat.messages


def test_chat_response(xession, monkeypatch_openai, chat):
    xession.env["OPENAI_API_KEY"] = "test"
    assert chat.chat_idx == 0
    chat.chat("test") == "test"
    assert chat.messages == [
        {"role": "user", "content": "test"},
        {"role": "assistant", "content": "test"},
    ]
    assert chat._tokens == [1, 1]
    assert chat.tokens == 55
    assert chat.chat_idx == -2


@pytest.mark.skip()
def test_trim(xession, chat):
    chat._tokens = [1000, 1000, 900]
    chat.messages = ["test", "test", "test"]
    chat._trim()
    assert len(chat._tokens) == 3
    chat._tokens.append(1000)
    chat.messages.append("test")
    chat._trim()
    assert len(chat._tokens) == 3
    assert len(chat.messages) == 3


def test_trim_convo(xession, chat):
    toks = chat._tokens = [1000, 1000, 900]
    idx = chat.chat_idx = -3
    chat.trim_convo()
    assert chat._tokens == toks
    assert chat.chat_idx == idx
    chat._tokens.append(1000)
    chat.chat_idx -= 1
    chat.trim_convo()
    assert chat._tokens == toks
    assert chat.chat_idx == idx


def test_set_base_msgs(xession, chat):
    assert chat._base_tokens == 53
    chat.base = [{"role": "system", "content": "test"}]
    assert chat._base_tokens == 8


def test__get_json_convo(xession, chat):
    chat.messages.append({"role": "user", "content": "test"})
    res = chat._get_json_convo(n=1)
    assert res == json.dumps([{"role": "user", "content": "test"}], indent=4)


@pytest.mark.parametrize(
    ("n", "n_expected", "color"), [(0, 5, True), (1, 1, True), (-1, 2, False)]
)
def test__get_printed_convo(xession, n, n_expected, color, chat):
    chat.messages.extend(
        [
            {"role": "user", "content": "test1"},
            {"role": "assistant", "content": "test2"},
            {"role": "user", "content": "`test3`"},
        ]
    )
    res = chat._get_printed_convo(n, color)
    assert len(res) == n_expected

    if color:
        assert "\x1b" in res[-1][1]
        assert "`" not in res[-1][1]
    else:
        assert "\x1b" not in res[-1][1]
        assert "`" in res[-1][1]


def test_print_convo_raises_no_convo_error(xession, chat):
    with pytest.raises(NoConversationsError):
        chat.print_convo(0)


def test_print_convo_raises_invalid_convo_error(xession, chat):
    chat.messages.append({"role": "user", "content": "test"})
    with pytest.raises(InvalidConversationsTypeError):
        chat.print_convo(0, mode="invalid")


@pytest.mark.parametrize(
    ("mode", "file"),
    [
        # ("color", "color_convo.txt"),
        ("text", "no_color_convo.txt"),
        ("json", "convo.json"),
    ],
)
def test_saves_convo(xession, chat, temp_home, mode, file, monkeypatch):
    monkeypatch.setenv("USER", "user")
    chat.messages.extend(
        [
            {"role": "user", "content": "Please write me a hello world function"},
            {"role": "assistant", "content": MARKDOWN_BLOCK_2},
        ]
    )
    chat.save_convo(temp_home / "saved" / file, mode=mode)
    assert (temp_home / "saved" / file).exists()
    with open(temp_home / "saved" / file, "r") as f:
        res = f.read().strip()
    with open(temp_home / "expected" / file, "r") as f:
        expected = f.read().strip()
    assert res == expected


def test_saves_with_override(xession, chat, temp_home, monkeypatch):
    monkeypatch.setenv("USER", "user")
    chat.messages.extend(
        [
            {"role": "user", "content": "Please write me a hello world function"},
            {"role": "assistant", "content": MARKDOWN_BLOCK_2},
            {"role": "user", "content": "test"},
        ]
    )
    chat.save_convo(temp_home / "test.txt", mode="json")
    with open(temp_home / "test.txt") as f:
        cur = json.load(f)
    chat.messages.pop()
    monkeypatch.setattr("builtins.input", lambda _: "y")
    chat.save_convo(temp_home / "test.txt", mode="json")
    with open(temp_home / "test.txt") as f:
        new = json.load(f)
    assert cur != new
    cur = new
    chat.messages.pop()
    chat.save_convo(temp_home / "test.txt", mode="json", override=True)
    with open(temp_home / "test.txt") as f:
        new = json.load(f)
    assert cur != new


@pytest.mark.parametrize(
    ("alias", "json", "name"),
    [
        (True, False, "my_chat"),
        (True, False, ""),
        (False, False, ""),
        (True, True, ""),
        (True, True, "my_chat"),
    ],
)
def test_saves_convo_to_default_location(
    xession, alias, json, name, chat, chat_w_alias, temp_home, monkeypatch
):
    monkeypatch.setenv("USER", "user")
    xession.env["XONSH_DATA_DIR"] = str(temp_home / "data_dir")
    now = datetime.now().strftime("%Y-%m-%d")
    convo = [
        {"role": "user", "content": "Please write me a hello world function"},
        {"role": "assistant", "content": MARKDOWN_BLOCK_2},
    ]
    current_chat = chat_w_alias if alias else chat
    current_chat.messages.extend(convo)
    prefix, ext, mode = (
        f'user_{name or current_chat.alias or "chatgpt"}_{now}',
        ".json" if json else ".txt",
        "json" if json else "text",
    )

    for i in range(3):
        current_chat.save_convo(name=name, mode=mode)
        if i == 0:
            assert (temp_home / "data_dir" / "chatgpt" / f"{prefix}{ext}").exists()
        else:
            assert (temp_home / "data_dir" / "chatgpt" / f"{prefix}_{i}{ext}").exists()


def test_auto_create_alias(xession):
    assert "chat" not in xession.aliases
    chat = ChatGPT("chat")
    assert "chat" in xession.aliases


def test_auto_del_alias(xession):
    chat = ChatGPT("chat")
    assert "chat" in xession.aliases
    del chat
    assert "chat" not in xession.aliases


def test_cli_execution(xession, chat_w_alias, capsys, monkeypatch_openai):
    xession.env["OPENAI_API_KEY"] = "test"
    xession.aliases["gpt"](["hello", "my", "name", "is", "user"])
    out, err = capsys.readouterr()
    out = out.strip().split("\n    ")
    assert "ChatGPT" in out[0]
    assert "test" in out[1]


def test_cli_execution_print(
    xession, chat_w_alias, capsys, monkeypatch, monkeypatch_openai
):
    monkeypatch.setattr(
        "xontrib_chatgpt.chatgpt.ChatGPT.print_convo",
        lambda _, n, mode: print("print_convo", n, mode),
    )
    xession.aliases["gpt"](["-p"])
    out, err = capsys.readouterr()
    assert out.strip() == "print_convo 10 color"
    xession.aliases["gpt"]("-p -n 5 -m no-color".split())
    out, err = capsys.readouterr()
    assert out.strip() == "print_convo 5 no-color"


def test_cli_execution_save(
    xession, chat_w_alias, capsys, monkeypatch, monkeypatch_openai
):
    monkeypatch.setattr(
        "xontrib_chatgpt.chatgpt.ChatGPT.save_convo",
        lambda _, path, name, mode: print("save_convo", path, name, mode),
    )
    xession.aliases["gpt"](["-s"])
    out, err = capsys.readouterr()
    assert out.strip() == "save_convo   text"
    xession.aliases["gpt"]("-s -P path -n 5 -t json --name name".split())
    out, err = capsys.readouterr()
    assert out.strip() == "save_convo path name json"


def test_cli_execution_pipe(xession, chat_w_alias, capsys, monkeypatch_openai):
    xession.env["OPENAI_API_KEY"] = "test"
    stdin = io.StringIO()
    stdin.write("hello")
    xession.aliases["gpt"]([], stdin=stdin)
    out, err = capsys.readouterr()
    out = out.strip().split("\n    ")
    assert "ChatGPT" in out[0]
    assert "test" in out[1]


def test_enter_exit(xession, chat, capsys, monkeypatch_openai):
    xession.env["OPENAI_API_KEY"] = "test"
    exe = xession.execer.exec
    exe("with! chat:\n    hello", glbs={"chat": chat})
    out, err = capsys.readouterr()
    out = out.strip().split("\n    ")
    assert "ChatGPT" in out[0]
    assert "test" in out[1]


def test_loads_from_convo(xession, temp_home):
    chat_file = temp_home / "expected" / "no_color_convo2.txt"
    new_cls = ChatGPT.fromconvo(chat_file)
    assert isinstance(new_cls, ChatGPT)
    assert new_cls.base[0] == {"role": "system", "content": "Test\n"}
    assert "Please write me a hello world function" in new_cls.messages[0]["content"]


def test_loads_from_convo_in_default_dir(xession, temp_home):
    xession.env["XONSH_DATA_DIR"] = str(temp_home / "data_dir")
    new_cls = ChatGPT.fromconvo("no_color_convo.txt")
    assert isinstance(new_cls, ChatGPT)
    assert "Please write me a hello world function" in new_cls.messages[0]["content"]


def test_loads_from_convo_raises_file_not_found(xession, temp_home):
    with pytest.raises(FileNotFoundError):
        ChatGPT.fromconvo("invalid.txt")


def test_loads_and_trims(xession, temp_home, monkeypatch):
    chat_file = temp_home / "expected" / "convo2.json"

    def trim_convo(self):
        while self.tokens > 650:
            self.chat_idx += 1

    monkeypatch.setattr("xontrib_chatgpt.chatgpt.ChatGPT.trim_convo", trim_convo)
    new_cls = ChatGPT.fromconvo(chat_file)
    assert new_cls.chat_idx == -1


@pytest.fixture
def inc_test(xession):
    xession.ctx["test"] = 0

    def _inc_test(**_):
        xession.ctx["test"] += 1

    return _inc_test


def test_on_chat_create_handler(xession, cm_events, inc_test):
    cm_events.on_chat_create(inc_test)
    inst = ChatGPT(managed=True)
    assert xession.ctx["test"] == 1


def test_on_chat_change(xession, cm_events, inc_test):
    cm_events.on_chat_create(inc_test)
    inst = ChatGPT(managed=True)
    assert xession.ctx["test"] == 1
    cm_events.on_chat_used(inc_test)
    inst([])
    assert xession.ctx["test"] == 2


def test_on_chat_destroy_handler(xession, cm_events, inc_test):
    cm_events.on_chat_create(inc_test)
    inst = ChatGPT(managed=True)
    assert xession.ctx["test"] == 1
    cm_events.on_chat_destroy(inc_test)
    del inst
    assert xession.ctx["test"] == 2
