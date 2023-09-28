"""Ideas for env handlers, currently not in use"""
from typing import Any, Callable
from xonsh.built_ins import XSH

class ChatEnv:
    """Helper class to improve efficiency in getting env variables"""

    # OPENAI_CHAT_MODEL: Callable[[], str] = lambda _: XSH.env.get('OPENAI_CHAT_MODEL', 'gpt-3.5-turbo')
    # OPENAI_API_KEY: Callable[[], str | None] = lambda _: XSH.env.get('OPENAI_API_KEY', None)
    OPENAI_CHAT_MODEL: str | None
    OPENAI_API_KEY: str | None

    # def __getattribute__(self, __name: str) -> Any:
    #     return super().__getattribute__(__name)
    
    def __contains__(self, key):
        return key in vars(self)
    
    @property
    def OPENAI_CHAT_MODEL(self) -> str:
        return XSH.env.get('OPENAI_CHAT_MODEL', 'gpt-3.5-turbo')
    
    @property
    def OPENAI_API_KEY(self) -> str | None:
        return XSH.env.get('OPENAI_API_KEY', None)

class Env:
    def __init__(self, loader: Callable[[], Any], ctx: dict, name: str):
        self._meta = { 'loader': loader, 'ctx': ctx, 'name': name }

    def obj(self):
        meta = self._meta
        obj = meta['loader']()
        return obj
    
    def __getattribute__(self, name):
        if name == 'obj' or name == '_meta':
            return super().__getattribute__(name)
        obj = self.obj()
        return getattr(obj, name)
    
    def __str__(self):
        return str(self.obj())
    
    def __eq__(self, other):
        return self.obj() == other

    def __ne__(self, other):
        obj = self.obj()
        return obj != other
    
    def __bool__(self):
        return bool(self.obj())

    def __iter__(self):
        obj = self.obj()
        yield from obj

def env(func: Callable[[], Any]) -> Env:
    return Env(func, func.__globals__, func.__name__)


# Cached concept
# class Env:
#     def __init__(self, loader, ctx, name):
#         self._obj = { 'loader': loader, 'valid': False, 'cached': None, 'name': name }
#     def obj(self):
#         print('Obj accessed')
#         d = self._obj
#         if d['valid']:
#             print(f'Valid - returning cached {d["cached"]}')
#             return d['cached']
#         print('Invalid - loading new')    
#         obj = d['loader']()
#         d['valid'] = True
#         d['cached'] = obj
#         print(f'New obj - {str(obj)}')
#         #d['ctx'][d['name']] = self
#         return obj
#     def __getattribute__(self, name):
#         if name in ['obj', '_obj', '_invalidate']:
#             print(f'Getting {name}')
#             return super().__getattribute__(name)
#         print('Getting obj')
#         obj = self.obj()
#         return getattr(obj, name)
#     def __str__(self):
#         return str(self.obj())
#     def __eq__(self, other):
#         return self.obj() == other
#     def __ne__(self, other):
#         return self.obj() != other
#     def __bool__(self):
#         return bool(self.obj())
#     def _invalidate(self, name, oldname, newname, **_):
#         d = self._obj
#         if name == d['name']:
#             print(f'Invalidating obj {name}')
#             d['valid'] = False
