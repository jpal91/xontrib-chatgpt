"""Module for ChatManager to manage multiple chats"""
import os
import weakref
from collections import defaultdict
from typing import Optional, Union, TextIO
from argparse import ArgumentParser
from re import Pattern

from xonsh.built_ins import XSH
from xonsh.ansi_colors import ansi_partial_color_format
from xonsh.lazyasd import LazyObject

from xontrib_chatgpt.chatgpt import ChatGPT
from xontrib_chatgpt.lazyobjs import _FIND_NAME_REGEX
from xontrib_chatgpt.args import _cm_parse

FIND_NAME_REGEX: Pattern = LazyObject(_FIND_NAME_REGEX, globals(), "FIND_NAME_REGEX")
PARSER: ArgumentParser = LazyObject(_cm_parse, globals(), "PARSER")

TUTORIAL = """
        {BOLD_WHITE}Usage of {BOLD_BLUE}chat-manager{RESET}
        {BOLD_WHITE}---------------------{RESET}

        First, start off by creating a new chat that we'll call 'gpt':
            {YELLOW}>>> {INTENSE_BLUE}chat-manager {INTENSE_GREEN}add {RESET}gpt
        
        This creates a new conversation with {INTENSE_BLUE}ChatGPT{RESET} which you can interact with.
        Any input and responses will be saved to this instance, so you can continue
        with your conversation as you please.

        From here, you have several ways to interact. The instance is created as 
        a {INTENSE_BLUE}Xonsh{RESET} alias, so you can simply call it as such:
            {YELLOW}>>> {INTENSE_BLUE}gpt{RESET} Hello, how are you?

        Since {INTENSE_BLUE}Xonsh{RESET} aliases can can interact with bash and xsh syntax, you can also
        use the following:
            {YELLOW}>>> {INTENSE_BLUE}echo{RESET} {INTENSE_YELLOW}'Hello, how are you?' {INTENSE_WHITE}| {INTENSE_BLUE}gpt{RESET}
            {YELLOW}>>> {INTENSE_BLUE}gpt{RESET} {INTENSE_WHITE}< {INTENSE_BLUE}echo{RESET} {INTENSE_YELLOW}'Hello, how are you?'
            {YELLOW}>>> {INTENSE_BLUE}cat{RESET} my_input.txt {INTENSE_WHITE}| {INTENSE_BLUE}gpt{RESET}
            {YELLOW}>>> {INTENSE_WHITE}my_input ={RESET} {INTENSE_YELLOW}"Hello, how are you?"
            {YELLOW}>>> {INTENSE_BLUE}echo {INTENSE_PURPLE}@({INTENSE_WHITE}my_input{INTENSE_PURPLE}) {INTENSE_WHITE}| {INTENSE_BLUE}gpt{RESET}
        
        Finally, the instance also acts as a {INTENSE_BLUE}Xonsh{RESET} context block:
            {YELLOW}>>> {INTENSE_GREEN}with{INTENSE_WHITE}! {INTENSE_BLUE}gpt{INTENSE_WHITE}:{RESET}
            {YELLOW}>>>{RESET}     Can you help me fix my python function?
            {YELLOW}>>>{RESET}     def hello_world():
            {YELLOW}>>>{RESET}         return
            {YELLOW}>>>{RESET}         print("Hello World!")
        
        Any content added to the context block will be sent to {INTENSE_BLUE}ChatGPT{RESET}, allowing
        you to send multi-line messages to {INTENSE_BLUE}ChatGPT{RESET}.

        Each conversation has a separate history, so if you want to start a new conversation on
        a different topic, simply create a new instance:
            {YELLOW}>>> {INTENSE_BLUE}chat-manager {INTENSE_GREEN}add {RESET}my_literature_convo

        {BOLD_WHITE}Other Useful Commands{RESET}
        {BOLD_WHITE}---------------------{RESET}

        Each conversation instance has it's own individual commands as well. Use the following
        to learn more about the options available to you:
            {YELLOW}>>> {INTENSE_BLUE}gpt {INTENSE_GREEN}-h{RESET}
        
        Print a conversation:
            {YELLOW}>>> {INTENSE_BLUE}gpt {INTENSE_GREEN}-p{RESET}
            {GREEN}# or{RESET}
            {YELLOW}>>> {INTENSE_BLUE}chat-manager {INTENSE_GREEN}print{RESET} gpt
        
        Save a conversation:
            {YELLOW}>>> {INTENSE_BLUE}my_literature_convo {INTENSE_GREEN}-s{RESET}
            {GREEN}# or{RESET}
            {YELLOW}>>> {INTENSE_BLUE}chat-manager {INTENSE_GREEN}save{RESET} my_literature_convo
        
        You can delete a conversation using {INTENSE_GREEN}Python{RESET} syntax:
            {YELLOW}>>> {INTENSE_PURPLE}del {INTENSE_BLUE}gpt{RESET}
        
        This will delete the instance, unsaved conversation history, and alias. Be careful!
"""

class ChatManager:
    """Class to manage multiple chats"""

    def __init__(self):
        self._instances: dict[int, dict[str, Union[str, ChatGPT]]] = defaultdict(dict)
        self._current: Optional[int] = None
        self._update_inst_dict()

    def __call__(self, args: list[str], stdin: TextIO = None):
        """Main method to interact with ChatManager via xonsh aliases"""
        if args:
            pargs = PARSER.parse_args(args)
        elif stdin:
            pargs = PARSER.parse_args(stdin.read().strip().split())
        else:
            return PARSER.print_help()

        if pargs.C:
            if self._current is None:
                return "No active chat!"
            else:
                return self._instances[self._current]["inst"].stats()

        if pargs.cmd in ["add", "a", "create"]:
            return self.add(pargs.name[0])
        elif pargs.cmd in ["list", "ls"]:
            return self.ls(saved=pargs.saved)
        elif pargs.cmd == "load":
            return self.load(pargs.name[0])
        elif pargs.cmd == "save":
            return self.save(chat_name=pargs.name, mode=pargs.mode)
        elif pargs.cmd in ["print", "p"]:
            return self.print_chat(chat_name=pargs.name, n=pargs.n, mode=pargs.mode)
        elif pargs.cmd == "help":
            return self.help(tgt=pargs.target)
        else:
            return PARSER.print_help()

    def add(self, chat_name: str) -> str:
        """Create new chat instance

        Parameters
        ----------
        chat_name : str
            Name of the chat instance to create

        Returns
        -------
        str
        """
        if chat_name in self.chat_names():
            return "Chat with that name already exists!"
        elif chat_name in XSH.ctx or chat_name in XSH.aliases:
            return "Variable with that name already exists!"
        inst = ChatGPT(alias=chat_name, managed=True)
        XSH.ctx[chat_name] = inst
        self._instances[hash(inst)]["name"] = chat_name
        return f"Created new chat {chat_name}"

    def ls(self, saved: bool = False) -> str:
        """List all active chats or saved chats

        Parameters
        ----------
        saved : bool, optional
            Whether to list saved chats or active chats, by default False

        Returns
        -------
        str
        """
        if saved:
            return (
                ansi_partial_color_format("{BOLD_WHITE}Saved chats:")
                + "\n  "
                + "\n  ".join(self._find_saved())
            )

        if not self._instances:
            return "No active chats."

        return "\n\n".join([inst["inst"].stats() for inst in self._instances.values()])

    def load(self, path_or_name: str) -> str:
        """Load a conversation from a path or a saved chat name

        Parameters
        ----------
        path_or_name : str
            Path to a conversation file or name of a saved chat

        Returns
        -------
        str
        """
        if os.path.exists(path_or_name):
            path, name = path_or_name, FIND_NAME_REGEX.sub(
                r"\1", os.path.basename(path_or_name)
            )
        else:
            path, name = self._find_path_from_name(path_or_name)

        curr_names = self.chat_names()

        if name in curr_names:
            idx = 0
            while name + str(idx) in curr_names:
                idx += 1
            print(
                f"Chat with name {name} already loaded. Updating to {name + str(idx)}"
            )
            name += str(idx)

        inst = ChatGPT.fromconvo(path, alias=name, managed=True)
        XSH.ctx[name] = inst
        self._instances[hash(inst)]["name"] = name

        return f"Loaded chat {name} from {path}"

    def save(self, chat_name: str = "", mode: str = "text") -> Optional[str]:
        """Save a conversation to a file

        Parameters
        ----------
        chat_name : str, optional
            Name of the chat to save. Defaults to last used/current chat, by default ''
        mode : str, optional
            Mode to save the conversation. Defaults to 'text', other option is 'json'

        Returns
        -------
        Optional[str]
        """

        if not chat_name and not self._current:
            return "No active chat!"
        elif not chat_name:
            chat = self._instances[self._current]
        else:
            try:
                chat = self._instances[hash(XSH.ctx[chat_name])]
            except KeyError:
                return f"No chat with name {chat_name} found."

        return chat["inst"].save_convo(mode=mode)

    def print_chat(
        self, chat_name: str = "", n: int = 10, mode: str = "color"
    ) -> Optional[str]:
        """Print a conversation

        Parameters
        ----------
        chat_name : str, optional
            Name of the chat to print. Defaults to last used/current chat, by default ''
        n : int, optional
            Number of conversations to print, by default 10
        mode : str, optional
            Mode to print the conversation. Defaults to 'color', other options are 'no-color' and 'json'

        Returns
        -------
        Optional[str]
        """

        if not chat_name and not self._current:
            return "No active chat!"
        elif not chat_name:
            chat = self._instances[self._current]
        else:
            try:
                chat = self._instances[hash(XSH.ctx[chat_name])]
            except KeyError:
                return f"No chat with name {chat_name} found."

        chat["inst"].print_convo(n=n, mode=mode)

    def help(self, tgt: str = "") -> Optional[str]:
        """Print help information on the instance, methods, or xontrib

        Parameters
        ----------
        tgt : str, optional
            Target to print help information on. Defaults to chat-manager, by default ''

        Returns
        -------
        Optional[str]
        """
        if not tgt:
            return self.tutorial()

        # TODO: Expand on this more
        if hasattr(self, tgt):
            XSH.help(getattr(self, tgt))
        elif hasattr(ChatGPT, tgt):
            XSH.help(getattr(ChatGPT, tgt))
        else:
            PARSER.print_help()

    def chat_names(self) -> list[str]:
        """Returns chat names for current conversations"""
        return [inst["name"] for inst in self._instances.values()]

    def _find_saved(self) -> list[Optional[str]]:
        """Returns a list of saved chat files in the default directory"""
        def_dir = os.path.join(XSH.env["XONSH_DATA_DIR"], "chatgpt")
        if not os.path.exists(def_dir):
            return []
        return [
            f for f in os.listdir(def_dir) if os.path.isfile(os.path.join(def_dir, f))
        ]

    def _find_path_from_name(self, name: str) -> tuple[str, str]:
        """Finds a saved chat file from user input if it's not a path"""
        def_dir = XSH.env["XONSH_DATA_DIR"]
        saved = self._find_saved()

        if name in saved:
            return os.path.join(def_dir, "chatgpt", name), FIND_NAME_REGEX.sub(
                r"\1", name
            )

        # Creates a tuple of (chat_name, file_name)
        names_saved = [
            (n, f)
            for n, f in [(FIND_NAME_REGEX.sub(r"\1", f), f) for f in saved]
            if n == name
        ]

        if not names_saved:
            raise FileNotFoundError(f"No chat with name {name} found.")
        elif len(names_saved) > 1:
            chat_name, file = self._choose_from_multiple(names_saved)
        else:
            chat_name, file = names_saved[0]

        return os.path.join(def_dir, "chatgpt", file), chat_name

    def _choose_from_multiple(self, chats: list[tuple[str, str]]) -> tuple[str, str]:
        """If multiple saved chats are found, allows the user to choose from them"""
        
        print("Multiple choices found, please choose from:")
        [print(f"  {i + 1}. {os.path.basename(n[1])}") for i, n in enumerate(chats)]

        while True:
            max_choice = len(chats)
            choice = input(f"Number (1 - {max_choice}): ")

            try:
                choice = int(choice)
            except ValueError:
                print("Invalid input, please enter a number.")
                continue

            if not 0 < choice <= max_choice:
                print(
                    f"Invalid input, please enter a number between 1 and {max_choice}."
                )
                continue

            return chats[choice - 1]

    def _update_inst_dict(self):
        """Finds all active instances (active convos) in the global space and updates the internal dict"""
        for key, inst in XSH.ctx.copy().items():
            if isinstance(inst, ChatGPT):
                self._instances[hash(inst)] = {
                    "name": key,
                    "alias": inst.alias,
                    "inst": weakref.proxy(inst),
                }

        if self._current not in self._instances:
            self._current = None

    def on_chat_create_handler(self, inst: ChatGPT) -> None:
        """Handler for on_chat_create. Updates the internal dict with the new chat instance."""
        self._current = hash(inst)
        
        # 'name' left blank because at this point the instance init isn't complete,
        # so variable name is not yet in the global space. 
        # Updated later in the add method
        self._instances[hash(inst)] = {
            "name": "", 
            "alias": inst.alias,
            "inst": weakref.proxy(inst),
        }

    def on_chat_destroy_handler(self, inst: ChatGPT) -> None:
        """Handler for on_chat_destroy. Removes the chat instance from the internal dict."""
        inst_hash = hash(inst)

        if inst_hash in self._instances:
            del self._instances[inst_hash]

        if inst_hash == self._current:
            self._current = None

    def on_chat_used_handler(self, inst: ChatGPT) -> None:
        """Handler for on_chat_used. Updates the current chat instance."""
        self._current = hash(inst)

    def tutorial(self) -> str:
        """Returns a usage string for the xontrib."""
        return ansi_partial_color_format(TUTORIAL)


# TODO: Print from a saved file
# TODO:
#   Save/Load name conflicts
#   Possibly add a flag to overwrite, or option to replace the old one
#   or Load chat with similar saved name into different variable name
#   ie load from 'path' into 'name'
