import json
import pytest
from textwrap import dedent

from xontrib_chatgpt.utils import (
    parse_convo,
    get_token_list,
    format_markdown,
    convert_to_sys,
)

@pytest.fixture
def sys_msgs():
    l = """[
    {'role': 'system', 'content': 'Hello'},
    {'role': 'system', 'content': 'Hi there!'},
    ]
    """

    d = '{"content": "Hello"}'

    y = dedent(
        """
    - role: system
      content: Hello
    - role: system
      content: Hi there!
    """
    )

    return l, d, y

MARKDOWN_BLOCK = """\
Hello!
```python
print('Hello World!')
```
"""

def test_format_markdown(xession):
    md = format_markdown(MARKDOWN_BLOCK)
    assert "\x1b" in md
    assert "```" not in md

def test_parses_json(xession, temp_home):
    json_path = temp_home / "expected" / "convo.json"
    with open(json_path) as f:
        exp_json = f.read()
    msg, base = parse_convo(exp_json)
    assert base + msg == json.loads(exp_json)


def test_parses_text(xession, temp_home):
    text_path = temp_home / "expected" / "long_convo.txt"
    with open(text_path) as f:
        exp_text = f.read()

    msgs, base = parse_convo(exp_text)
    assert len(msgs) == 6
    assert len(base) == 1

    for r in msgs:
        assert r["role"] in ["user", "assistant"]
        assert r["content"] != ""
    
    assert base[0] == {'role': 'system', 'content': 'This is a test.\n'}

def test_get_token_list(xession, temp_home):
    json_path = temp_home / "expected" / "convo2.json"
    with open(json_path) as f:
        exp_json = json.load(f)
    res = get_token_list(exp_json)
    assert len(res) == 7
    assert sum(res) == 835

def test_convert_to_sys(xession, sys_msgs):
    l, d, y = sys_msgs
    res = convert_to_sys(l)
    assert res == [
        {"role": "system", "content": "Hello"},
        {"role": "system", "content": "Hi there!"},
    ]
    res = convert_to_sys(d)
    assert res == [{"role": "system", "content": "Hello"}]
    res = convert_to_sys(y)
    assert res == [
        {"role": "system", "content": "Hello"},
        {"role": "system", "content": "Hi there!"},
    ]