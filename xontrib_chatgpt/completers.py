from xonsh.built_ins import XSH
from xonsh.completers.completer import add_one_completer, remove_completer
from xonsh.completers.tools import RichCompletion, contextual_command_completer_for, contextual_completer
from xonsh.parsers.completion_context import CommandContext, CompletionContext

from xontrib_chatgpt.chatmanager import ChatManager 


@contextual_command_completer_for("chat-manager")
def cm_completer(command: CommandContext) -> set[RichCompletion]:
    """Completions for chat-manager"""
    opts_desc = {
        "add": "Add/Create a new chat",
        "list": "List all current or saved chats",
        "save": "Save a chat to a local file",
        "load": "Load a chat from a local file",
        "print": "Print a chat to the console",
    }
    if command.arg_index < 2:
        return {
                RichCompletion(k, description=v, append_space=True)
                for k, v in opts_desc.items()
                if k.startswith(command.prefix)
            }

@contextual_completer
def print_save_chat_completer(command: CompletionContext) -> set[str]:
    """Completions for chat-manager print"""

    if (
        command.command and
        command.command.arg_index == 2 and
        command.command.args[0].value == 'chat-manager' and
        command.command.args[1].value in ['print', 'save']
    ):
        cm: ChatManager = XSH.ctx['chat_manager']

        return {
                *cm.chat_names()
            }



@contextual_completer
def load_chat_completer(context: CompletionContext) -> set[str]:
    """Completions for chat-manager load"""
    
    if (
        context.command and
        context.command.arg_index == 2 and
        context.command.args[0].value == 'chat-manager' and
        context.command.args[1].value == 'load'
    ):
        cm: ChatManager = XSH.ctx['chat_manager']

        return {
                *cm._find_saved()
            }

def add_completers() -> None:
    add_one_completer("chat-manager", cm_completer, loc="start")
    add_one_completer('cm-load', load_chat_completer, loc='start')
    add_one_completer('cm-print', print_save_chat_completer, loc='start')

def rm_completers() -> None:
    remove_completer("chat-manager")
    remove_completer('cm-load')
    remove_completer('cm-print')