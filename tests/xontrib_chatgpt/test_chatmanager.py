import pytest
from xontrib_chatgpt.chatmanager import ChatManager
from xontrib_chatgpt.chatgpt import ChatGPT

@pytest.fixture(scope='module')
def temp_home(tmp_path_factory):
    home = tmp_path_factory.mktemp('home')
    (home / 'data_dir').mkdir()
    (home / 'data_dir' / 'chatgpt').mkdir()
    (home / 'data_dir' / 'chatgpt' / 'dummy').mkdir()
    return home

@pytest.fixture(autouse=True)
def data_dir(xession, temp_home):
    xession.env['XONSH_DATA_DIR'] = str(temp_home / 'data_dir')

@pytest.fixture
def test_files(temp_home):
    test_files = ['test1.txt', 'test2.txt', 'test3.txt']
    [(temp_home / 'data_dir' / 'chatgpt' / f).touch() for f in test_files]
    yield test_files
    [(temp_home / 'data_dir' / 'chatgpt' / f).unlink() for f in test_files]

@pytest.fixture
def cm():
    return ChatManager()

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

def test_add_with_conflicting_name(xession, cm):
    cm.add('test')
    res = cm.add('test')
    assert res == 'Chat with that name already exists!'


def test_ls(xession, cm_events, cm, monkeypatch, capsys):
    monkeypatch.setattr('xontrib_chatgpt.chatgpt.ChatGPT.__str__', lambda *_, **__: 'test_out')
    cm_events.on_chat_create(lambda *args, **kw: cm._on_chat_create(*args, **kw))
    cm.add('test1')
    cm.add('test2')
    assert len(cm._instances.keys()) == 2
    cm.ls()
    out, err = capsys.readouterr()
    assert out.strip() == 'Name: test1\ntest_out\n\nName: test2\ntest_out'

def test_find_saved(xession, cm, temp_home, test_files):
    res = cm._find_saved()
    assert len(res) == 3
    assert sorted(res) == test_files

@pytest.mark.parametrize(
    ('input', 'fname','name'),
    [
        ('test1', 'something_test1.txt','test1'),
        ('something_test2_01-02-03.json','something_test2_01-02-03.json','test2'),
        ('test3', 'test3.txt', 'test3'),
    ],
)
def test_find_path_from_name(xession, cm, input, fname, name, temp_home):
    data_dir = temp_home / 'data_dir'
    chat_dir = data_dir / 'chatgpt'
    (chat_dir / fname).touch()
    res = cm._find_path_from_name(input)
    assert res == (str(chat_dir / fname), name)
    (chat_dir / fname).unlink()

def test_choose_from_multiple(xession, cm, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda *_, **__: '2')
    res = cm._choose_from_multiple([('test1', 'file1'), ('test2', 'file2')])
    assert res == ('test2', 'file2')

@pytest.mark.parametrize(
    ('inp', 'name'),
    [
        ('data_dir/chatgpt/test1.txt', 'test1'),
        ('test2.txt', 'test2'),
        ('test3', 'test3'),
    ]
)
def test_load(xession, cm, inp, name, temp_home, test_files):
    data_dir = temp_home / 'data_dir'
    inp = inp.replace('data_dir', str(data_dir))
    res = cm.load(inp)
    assert name in xession.ctx
    assert f'Loaded chat {name}' in res

def test_load_with_conflicting_name(xession, cm, test_files, temp_home):
    cm.add('test1')
    res = cm.load('test1')
    assert 'Loaded chat test10' in res
    assert 'test10' in xession.ctx
    assert 'test1' in xession.ctx