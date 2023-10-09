# Tips and Tricks

Just a few notes on some QOL things that are added, or can be added to `xontrib-chatgpt`

## Completions

**Added as of v0.1.5**

To see all available command line options for `chat-manager`:
```xsh
chat-manager <TAB>
```

The following will show a completion with all available files in the default `XONSH_DATA_DIR/chatgpt` that can be loaded:
```xsh
chat-manager load <TAB>
```

The following shows all existing chats that can be saved or printed to the command line:
```
chat-manager save <TAB>
chat-manager print <TAB>
```

## Custom Key Bindings

It's a little rough around the edges, but this keybinding turns a single-line prompt into a multi-line one.

This is for situations where you start typing the prompt as single-line, but realize you actually wanted it to be a multi-line half way through.

You will have to manually load this into your `.xonshrc`

```python
from xonsh.built_ins import XSH
from xonsh.events import events
from prompt_toolkit.filters import Condition

@events.on_ptk_create
def custom_keybindings(bindings, **kwargs):

    @Condition
    def multiline_convert():
        buffer = XSH.shell.shell.prompter.default_buffer
        first_line = buffer.document.line_count == 1
        return first_line and buffer.document.text
    
    @bindings.add('escape', 'm', filter=multiline_convert)
    def switch_to_multiline_on_chat(event):
        buffer = event.current_buffer
        curr_pos = buffer.cursor_position

        buffer.cursor_position = 0
        st, end = buffer.document.find_boundaries_of_current_word()
        word = buffer.document.text[st:end]

        if word not in XSH.ctx:
            buffer.cursor_position = curr_pos
            return
        
        buffer.delete(count=len(word))
        buffer.insert_text(f'with! {word}:\n    ')
        buffer.cursor_position = curr_pos + 12
```

This allows for:
```xsh
# Oh darn, I forgot I wanted to include my broken function in the prompt...
gpt Hello can you help me fix my python function?<ALT+M>

# to become
with! gpt:
    Hello can you help me fix my python function?
    ... # Your broken function here
```