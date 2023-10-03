import pytest
from xontrib_chatgpt.chatmanager import ChatManager
from xontrib_chatgpt.chatgpt import ChatGPT



def test_update_inst_dict(xession):
    cm = ChatManager()
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

def test_on_chat_create(xession, cm_events):
    cm = ChatManager()
    inst = ChatGPT('test_alias')
    xession.ctx['test_name'] = inst
    cm_events.on_chat_create(lambda *args, **kw: cm._on_chat_create(*args, **kw))
    cm_events.on_chat_create.fire(inst_hash=hash(inst))
    assert cm._current == hash(inst)
    assert hash(inst) in cm._instances
    assert cm._instances[hash(inst)]['name'] == 'test_name'
    assert cm._instances[hash(inst)]['alias'] == 'test_alias'
    assert cm._instances[hash(inst)]['inst'] == inst

def test_on_chat_destroy(xession, cm_events):
    cm = ChatManager()
    inst = ChatGPT('test')
    xession.ctx['test'] = inst
    cm._update_inst_dict()
    cm._current = hash(inst)
    cm_events.on_chat_destroy(lambda *args, **kw: cm._on_chat_destroy(*args, **kw))
    cm_events.on_chat_destroy.fire(inst_hash=hash(inst))
    assert cm._current is None
    assert hash(inst) not in cm._instances

def test_on_chat_used(xession, cm_events):
    cm = ChatManager()
    assert cm._current is None
    cm_events.on_chat_used(lambda *args, **kw: cm._on_chat_used(*args, **kw))
    cm_events.on_chat_used.fire(inst_hash=1)
    assert cm._current == 1