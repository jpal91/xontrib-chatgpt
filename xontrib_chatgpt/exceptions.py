"""Exceptions for the ChatGPT class"""

#############
# Exceptions
#############
class NoApiKeyError(Exception):
    """Raised when no API key is found"""

    def __init__(self, *_):
        pass

    def __str__(self):
        return "\n\x1b[1;31mNo OpenAI API key found"


class UnsupportedModelError(Exception):
    """Raised when an unsupported model is used"""

    def __init__(self, msg: str, *_):
        self.msg = msg

    def __str__(self):
        return f"\n\x1b[1;31m{self.msg}"


class NoConversationsError(Exception):
    """Raised when attempting to print/save a conversation when there is no conversation history"""

    def __init__(self, *_):
        pass

    def __str__(self):
        return "\n\x1b[1;31mNo conversation history!"


class InvalidConversationsTypeError(Exception):
    """Raised when attempting to print/save a conversation with an invalid type"""

    def __init__(self, msg: str, *_):
        self.msg = msg

    def __str__(self):
        return f"\n\x1b[1;31m{self.msg}"


#############