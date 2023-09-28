import io
import json
import shutil
import pytest
from xonsh.tools import indent
from xontrib.chatgpt import (
    ChatGPT,
    NoApiKeyError,
    UnsupportedModelError,
    ChatEnv,
    env_handler,
    NoConversationsError,
    InvalidConversationsTypeError
)


#############
# ChatGPT Class
#############

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
            "usage": {"total_tokens": 1},
        }


@pytest.fixture(autouse=True)
def env_class(xession):
    env = ChatEnv()
    lambda_envhandler = lambda name, oldvalue, newvalue, **_: env_handler(
        name, oldvalue, newvalue, env
    )
    xession.env["OPENAI_API_KEY"] = "dummy"
    env.OPENAI_API_KEY = "dummy"
    xession.env["OPENAI_CHAT_MODEL"] = "gpt-3.5-turbo"
    xession.builtins.events.on_envvar_change(lambda_envhandler)
    xession.ctx["chat_env"] = env
    yield


@pytest.fixture(scope='module')
def temp_home(tmpdir_factory):
    home = tmpdir_factory.mktemp('home')
    home.mkdir('expected')
    home.mkdir('saved')
    fixtures = ['color_convo.txt', 'no_color_convo.txt', 'convo.json']
    for f in fixtures:
        shutil.copy(f'tests/fixtures/{f}', f'{home}/expected/{f}')
    yield home

@pytest.fixture
def monkeypatch_openai(monkeypatch):
    dummy_ai = DummyAI()
    dummy_ai.ChatCompletion = DummyAI()
    monkeypatch.setattr("xontrib.chatgpt.openai", dummy_ai)

@pytest.fixture
def chat(xession):
    return ChatGPT()

@pytest.fixture
def chat_w_alias(xession):
    chat = ChatGPT('gpt')
    yield chat
    del chat

def test_alias_creation(xession):
    assert "chat" not in xession.aliases
    chat = ChatGPT()
    assert "chat" not in xession.aliases
    chat = ChatGPT("chat")
    assert "chat" in xession.aliases
    del xession.aliases["chat"]


def test_defualt_attribs(xession, chat):
    assert chat.base == [{"role": "system", "content": "You are a helpful assistant."}]
    assert chat.messages == []
    assert chat._tokens == []
    assert chat._max_tokens == 3000
    assert chat.alias == ""
    assert chat.tokens == 0


def test_tokens(xession, chat):
    chat._tokens = [1, 2, 3]
    assert chat.tokens == 6


def test_chat_raises_error_with_no_api_key(xession, chat):
    xession.env["OPENAI_API_KEY"] = ""
    with pytest.raises(NoApiKeyError):
        chat.chat("test")


def test_chat_raises_error_with_no_chat_model(xession, chat):
    xession.env["OPENAI_CHAT_MODEL"] = "test"
    with pytest.raises(UnsupportedModelError):
        chat.chat("test")


def test_chat_response(xession, monkeypatch_openai, chat):
    chat.chat("test") == "test"
    assert chat.messages == [
        {"role": "user", "content": "test"},
        {"role": "assistant", "content": "test"},
    ]
    assert chat._tokens == [1]
    assert chat.tokens == 1


def test_trim(xession, chat):
    chat._tokens = [1000, 1000, 1000]
    chat._trim()
    assert len(chat._tokens) == 3
    chat._tokens.append(1000)
    chat.messages.append("test")
    chat._trim()
    assert len(chat._tokens) == 3
    assert len(chat.messages) == 0

def test__format_markdown(xession, chat):
    md = chat._format_markdown(MARKDOWN_BLOCK)
    assert '\x1b' in md
    assert '```' not in md

def test__get_json_convo(xession, chat):
    chat.messages.append({"role": "user", "content": "test"})
    res = chat._get_json_convo(n=1)
    assert res == json.dumps([{"role": "user", "content": "test"}], indent=4)


@pytest.mark.parametrize(
    ('n', 'n_expected', 'color'),
    [
        (0, 3, True),
        (1, 1, True),
        (-1, 2, False)
    ]
)
def test__get_printed_convo(xession, n, n_expected, color, chat):
    chat.messages.extend([
        {"role": "user", "content": "test1"},
        {"role": "assistant", "content": "test2"},
        {"role": "user", "content": "`test3`"},
    ])
    res = chat._get_printed_convo(n, color)
    assert len(res) == n_expected

    if color:
        assert '\x1b' in res[-1][1]
        assert '`' not in res[-1][1]
    else:
        assert '\x1b' not in res[-1][1]
        assert '`' in res[-1][1]

def test_print_convo_raises_no_convo_error(xession, chat):
    with pytest.raises(NoConversationsError):
        chat.print_convo(0)

def test_print_convo_raises_invalid_convo_error(xession, chat):
    chat.messages.append({"role": "user", "content": "test"})
    with pytest.raises(InvalidConversationsTypeError):
        chat.print_convo(0, mode='invalid')

@pytest.mark.parametrize(
    ('mode', 'file'),
    [
        ('color', 'color_convo.txt'),
        ('no-color', 'no_color_convo.txt'),
        ('json', 'convo.json')
    ]
)
def test_saves_convo(xession, chat, temp_home, mode, file, monkeypatch):
    monkeypatch.setenv('USER', 'user')
    chat.messages.extend([
        {"role": "user", "content": "Please write me a hello world function"},
        {"role": "assistant", "content": MARKDOWN_BLOCK_2},
    ])
    chat.save_convo(temp_home / 'saved' / file, mode=mode)
    assert (temp_home / 'saved' / file).exists()
    with open(temp_home / 'saved' / file, 'r') as f:
        res = f.read()
    with open(temp_home / 'expected' / file, 'r') as f:
        expected = f.read()
    assert res == expected

def test_auto_create_alias(xession):
    assert 'chat' not in xession.aliases
    chat = ChatGPT('chat')
    assert 'chat' in xession.aliases

def test_auto_del_alias(xession):
    chat = ChatGPT('chat')
    assert 'chat' in xession.aliases
    del chat
    assert 'chat' not in xession.aliases

def test_cli_execution(xession, chat_w_alias, capsys, monkeypatch_openai):
    xession.aliases['gpt'](['hello', 'my', 'name', 'is', 'user'])
    out, err = capsys.readouterr()
    out = out.strip().split('\n    ')
    assert 'ChatGPT' in out[0]
    assert 'test' in out[1]
    
def test_cli_execution_pipe(xession, chat_w_alias, capsys, monkeypatch_openai):
    stdin = io.StringIO()
    stdin.write('hello')
    xession.aliases['gpt']([], stdin=stdin)
    out, err = capsys.readouterr()
    out = out.strip().split('\n    ')
    assert 'ChatGPT' in out[0]
    assert 'test' in out[1]

def test_enter_exit(xession, chat, capsys, monkeypatch_openai):
    exe = xession.execer.exec
    exe('with! chat:\n    hello', glbs={'chat': chat})
    out, err = capsys.readouterr()
    out = out.strip().split('\n    ')
    assert 'ChatGPT' in out[0]
    assert 'test' in out[1]
