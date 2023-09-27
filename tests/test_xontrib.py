import pytest
from xontrib.chatgpt import (
    ChatEnv,
    env_handler
)

def test_it_loads(load_xontrib):
    load_xontrib("chatgpt")

#############
# Env Handlers
#############
@pytest.fixture()
def reset_env(xession):
    yield
    if "OPENAI_API_KEY" in xession.env:
        del xession.env["OPENAI_API_KEY"]
    if "OPENAI_CHAT_MODEL" in xession.env:
        del xession.env["OPENAI_CHAT_MODEL"]


def test_chatenv_loads(xession, reset_env):
    chatenv = ChatEnv()
    assert chatenv.OPENAI_API_KEY == None
    assert chatenv.OPENAI_CHAT_MODEL == "gpt-3.5-turbo"

def test_chatenv_contains(xession, reset_env):
    chatenv = ChatEnv()
    assert "OPENAI_API_KEY" in chatenv
    assert "OPENAI_CHAT_MODEL" in chatenv
    assert "OPENAI_CHAT_MODEL2" not in chatenv
    assert len(vars(chatenv)) == 2

def test_env_handler_updates(xession, reset_env):
    chatenv = ChatEnv()
    env_handler("OPENAI_API_KEY", None, "test", chatenv)
    env_handler("OPENAI_CHAT_MODEL", "gpt-3.5-turbo", "test", chatenv)
    assert chatenv.OPENAI_API_KEY == "test"
    assert chatenv.OPENAI_CHAT_MODEL == "test"

def test_env_handler_updates_on_fire(xession, reset_env):
    chat_env = ChatEnv()
    xession.env['OPENAI_API_KEY'] = 'test'
    xession.env['OPENAI_CHAT_MODEL'] = 'test'
    lambda_envhandler = lambda name, oldvalue, newvalue, **_: env_handler(name, oldvalue, newvalue, chat_env)
    xession.builtins.events.on_envvar_change(lambda_envhandler)
    xession.env['OPENAI_API_KEY'] = 'test_fire'
    xession.env['OPENAI_CHAT_MODEL'] = 'test_fire'
    assert chat_env.OPENAI_API_KEY == 'test_fire'
    assert chat_env.OPENAI_CHAT_MODEL == 'test_fire'
    xession.builtins.events.on_envvar_change.remove(lambda_envhandler)

#############


#############
# ChatGPT Class
#############