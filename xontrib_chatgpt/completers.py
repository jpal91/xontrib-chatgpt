from xonsh.completers.tools import RichCompletion, contextual_command_completer_for
from xonsh.parsers.completion_context import CommandContext


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

    if not command.prefix:
        return {
            *[
                RichCompletion(k, description='v', append_space=True)
                for k, v in opts_desc.items()
            ]
        }
    else:
        return {
            *[
                RichCompletion(k, description=v, append_space=True)
                for k, v in opts_desc.items()
                if k.startswith(command.prefix)
            ]
        }
