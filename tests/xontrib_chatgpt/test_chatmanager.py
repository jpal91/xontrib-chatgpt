import pytest
from xontrib_chatgpt.chatmanager import ChatManager
from xontrib_chatgpt.chatgpt import ChatGPT

@pytest.fixture
def cm():
    return ChatManager()

@pytest.fixture(scope='module')
def temp_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('home')
    (home / 'data_dir').mkdir()
    (home / 'data_dir' / 'chatgpt').mkdir()
    (home / 'data_dir' / 'chatgpt' / 'dummy').mkdir()
    return home


def test_update_inst_dict(xession, cm):
    insts = [
        ('test', ChatGPT('test')),
        ('test1', ChatGPT('test1')),
        ('test2', ChatGPT('test2')),
    ]
    for inst in insts:
        xession.ctx[inst[0]] = inst[1]

    cm._update_inst_dict()

    for inst in insts:
        assert hash(inst[1]) in cm._instances
        assert cm._instances[hash(inst[1])]['name'] == inst[0]
        assert cm._instances[hash(inst[1])]['alias'] == inst[1].alias
        assert cm._instances[hash(inst[1])]['inst'] == inst[1]

def test_on_chat_create(xession, cm_events, cm):
    inst = ChatGPT('test_alias')
    xession.ctx['test_name'] = inst
    cm_events.on_chat_create(lambda *args, **kw: cm._on_chat_create(*args, **kw))
    cm_events.on_chat_create.fire(inst=inst)
    assert cm._current == hash(inst)
    assert hash(inst) in cm._instances
    assert cm._instances[hash(inst)]['alias'] == 'test_alias'
    assert cm._instances[hash(inst)]['inst'] == inst

def test_on_chat_destroy(xession, cm_events, cm):
    inst = ChatGPT('test')
    xession.ctx['test'] = inst
    cm._update_inst_dict()
    cm._current = hash(inst)
    cm_events.on_chat_destroy(lambda *args, **kw: cm._on_chat_destroy(*args, **kw))
    cm_events.on_chat_destroy.fire(inst_hash=hash(inst))
    assert cm._current is None
    assert hash(inst) not in cm._instances

def test_on_chat_used(xession, cm_events, cm):
    assert cm._current is None
    cm_events.on_chat_used(lambda *args, **kw: cm._on_chat_used(*args, **kw))
    cm_events.on_chat_used.fire(inst_hash=1)
    assert cm._current == 1

def test_add(xession, cm):
    cm.add('test')
    assert 'test' in xession.ctx
    assert isinstance(xession.ctx['test'], ChatGPT)
    assert 'test' in xession.aliases

def test_ls(xession, cm_events, cm, monkeypatch, capsys):
    monkeypatch.setattr('xontrib_chatgpt.chatgpt.ChatGPT.__str__', lambda *_, **__: 'test_out')
    cm_events.on_chat_create(lambda *args, **kw: cm._on_chat_create(*args, **kw))
    cm.add('test1')
    cm.add('test2')
    assert len(cm._instances.keys()) == 2
    cm.ls()
    out, err = capsys.readouterr()
    assert out.strip() == 'Name: test1\ntest_out\n\nName: test2\ntest_out'

def test_find_saved(xession, cm, temp_home):
    data_dir = xession.env['XONSH_DATA_DIR'] = str(temp_home / 'data_dir')
    test_files = ['test1.txt', 'test2.txt', 'test3.txt']
    [(temp_home / 'data_dir' / 'chatgpt' / f).touch() for f in test_files]
    res = cm._find_saved()
    assert len(res) == 3
    assert sorted(res) == test_files