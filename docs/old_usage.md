## Prior Version Usage

`xontrib-chatgpt` was designed to be versatile. To that end, it has capabilities of a `python` function, a `bash`-like function, and a `xonsh` context block.

#### Basic

When loaded, an alias `chatgpt` will automatically be added into your shell. You can use this for simple one-off questions -

```xsh
chatgpt Can you write me a simple 'hello world' function in python?
# ChatGPT responds here
```

#### Context Manager

To carry on a conversation with `ChatGPT`, first assign the `ChatGPT` class to a variable

```py
gpt = ChatGPT()
```

This package extends the built-in `Block` context manager capabilities from `xonsh`, allowing for multi-line inputs to be sent to the `ChatGPT` api

```xsh
with! gpt:
   My python function below is broken, can you help me fix it?

   def hello_world():
      return None
      print('Hello world!')

# ChatGPT responds here
# Any other inputs added will be included in the messages sent to ChatGPT

with! gpt:
   ...
```

#### With Alias

To unlock the full range of conversation options, you can optionally assign an `alias` to the instance -

```xsh
# Best practice is to use the same name as your variable assignment
gpt = ChatGPT(alias='gpt')

# The following is automatically ran for you...
# aliases['gpt'] = lambda args, stdin=None: gpt(args, stdin)

# Then use as a context manager...
with! gpt:
   Hello! Tell me more about yourself.

# Or as an alias function...
gpt Hello! Tell me more about yourself.
echo 'Hello! Tell me more about yourself.' | gpt

# Go crazy with it!
cat my_input.txt | gpt
my_next_input = $(echo 'Hello! Tell me more about yourself')
echo @(my_next_input) | gpt
```

When your variable/conversation is deleted, the registered `alias` is automatically deleted as well

```xsh
del gpt
Deleting alias gpt
```

### Get Help

For class/instance related help -

```xsh
ChatGPT?
gpt = ChatGPT()
gpt?
```

For cli related help
```xsh
chatgpt -h
gpt = ChatGPT()
gpt -h
```

### Additional Capabilities

#### Printing Convo

To print out your conversation to the shell, use one of the following -

```xsh
gpt = ChatGPT('gpt')

gpt.print_convo()
# or
gpt -p
```

See `gpt -h` or `gpt.print_convo?` for additional help and options

#### Saving Convo

To save your current conversation -

```xsh
gpt = ChatGPT('gpt')

gpt.save_convo(path='path/to/my_convo.txt')
# or
gpt -s -P 'path/to/my_convo.txt'
```

See `gpt -h` or `gpt.save_convo?` for additional help and options

#### Loading Convo

You can load a past conversation to a variable using the class method `ChatGPT.fromconvo`

```xsh
gpt = ChatGPT.fromconvo(path='path/to/my_convo.txt', alias='gpt')
```

#### Version 0.1.3 Notes
- `chat-manager` is meant to replace prior direct usage of utilizing the `ChatGPT` python class directly
- Direct usage of `ChatGPT` will not be deprecated, yet, but the plan is to have `chat-manager` be the defacto usage of this package
- `chat-manager` is also getting passed to the global ctx for debugging purposes for now as `chat_manager`, but will later be deprecated
- The one-off alias `chatgpt` is also available, but will be deprecated in later versions
- To see the original documentation on these, please visit the [old usage](/docs/old_usage.md) docs
- Three new `xonsh` events were added to help manage changes see [events](/docs/events.md) for details