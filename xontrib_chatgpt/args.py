"""Argument parsers for ChatGPT and ChatManager"""
from argparse import ArgumentParser


def _gpt_parse():
    """Argument parser for chatgpt"""
    cmd_parser = ArgumentParser(
        prog="chatgpt", description="Chat with OpenAI's ChatGPT from the command line"
    )
    cmd_parser.set_defaults(cmd="send")
    p_group = cmd_parser.add_argument_group(title="Print")
    p_group.add_argument(
        "-p",
        "--print",
        dest="cmd",
        const="print",
        action="store_const",
        help="Prints the conversation",
    )
    p_group.add_argument(
        "-n",
        type=int,
        default=10,
        help="Number of messasges to print. Default is 10. Use 0 for all.",
    )
    p_group.add_argument(
        "-m",
        "--mode",
        type=str,
        default="color",
        choices=["color", "no-color", "json"],
        help="Mode to print or save the conversation. Default is color",
    )
    s_group = cmd_parser.add_argument_group(title="Save")
    s_group.add_argument(
        "-s",
        "--save",
        dest="cmd",
        const="save",
        action="store_const",
        help="Saves the conversation",
    )
    s_group.add_argument(
        "-P",
        "--path",
        type=str,
        default="",
        help="File path to save the conversation. Default is $XONSH_DATA_DIR/chatgpt.",
    )
    s_group.add_argument(
        "--name",
        type=str,
        default="",
        help="Name of the conversation file. Default is chatgpt. Ignored when path is specified.",
    )
    s_group.add_argument(
        "-t",
        "--type",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Type of the conversation file. Default is text.",
    )
    cmd_parser.add_argument(
        "text",
        nargs="*",
        default=None,
        help="Text to send to ChatGPT. Will be ignored when other cmd is used.",
    )

    return cmd_parser


def _cm_parse() -> ArgumentParser:
    """Argument parser for chat-manager"""
    parser = ArgumentParser(
        prog="chat-manager",
        description="Chat with OpenAI's ChatGPT from the command line",
    )
    parser.add_argument(
        "-C",
        help="Print information on the current/last used chat and exit",
        const=True,
        default=False,
        action="store_const",
    )

    subparser = parser.add_subparsers(
        dest="cmd", title="Available Commands", metavar="COMMAND"
    )

    p_add = subparser.add_parser(
        "add", help="Add/Create a chat", aliases=["a", "create"]
    )
    p_add.add_argument("name", type=str, help="Name of the chat to create", nargs=1)

    p_list = subparser.add_parser(
        "list", help="List all current or saved chats", aliases=["ls"]
    )
    p_list.add_argument(
        "-s",
        "--saved",
        action="store_true",
        help="List all saved chats from the default directory",
    )

    p_load = subparser.add_parser("load", help="Load a saved chat")
    p_load.add_argument(
        "name", type=str, help="Name or absolute path of the chat to load", nargs=1
    )

    p_save = subparser.add_parser("save", help="Save a chat")
    p_save.add_argument(
        "name",
        type=str,
        default="",
        help="Name of the chat to save. Defaults to last used/current chat",
        nargs="?",
    )
    p_save.add_argument(
        "-m",
        "--mode",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Mode to print or save the conversation. Default is text",
    )

    p_print = subparser.add_parser("print", help="Print a chat", aliases=["p"])
    p_print.add_argument(
        "name",
        type=str,
        help="Name of the chat to print. Defaults to last used/current chat",
        nargs="?",
        default="",
    )
    p_print.add_argument(
        "-n", type=int, default=10, help="Number of conversations to print"
    )
    p_print.add_argument(
        "-m",
        "--mode",
        type=str,
        default="color",
        choices=["color", "no-color", "json"],
        help="Mode to print or save the conversation. Default is color",
    )

    p_help = subparser.add_parser("help", help="Print help information", epilog="hello")
    p_help.add_argument(
        "target",
        type=str,
        default="",
        help="Target to print help information on. Defaults to chat-manager",
        nargs="?",
    )

    return parser


if __name__ == "__main__":
    parser = _cm_parse()
    args = parser.parse_args(["help", "-h"])
    print(args)
