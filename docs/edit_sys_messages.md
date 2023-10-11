# Edit System Messages

## Introduction

> [!NOTE]
> From [OpenAI Documentation](https://platform.openai.com/docs/guides/gpt/chat-completions-api):
> 
> The system message helps set the behavior of the assistant. For example, you can modify the personality of the assistant or provide specific instructions about how it should behave throughout the conversation. 
> However note that the system message is optional and the model’s behavior without a system message is likely to be similar to using a generic message such as "You are a helpful assistant."

Per the definition, system messages are a set of instructions on how the model is supposed to behave or react to your input. This can be helpful if you want to put a *theme* on your conversation.

Below is an example of a system message, this is actually the default added to each `chat-manager` instance (formatted for readability):

```python
{
    "role": "system", 
    "content": "You are a helpful assistant."
},
{
    "role": "system",
    "content": """
    If your responses include code, make sure to wrap it in a markdown code block with the appropriate language.
    Example:
    ```python
    print('Hello World!')
    ```
    """
}
```

As you can see, the instance is given a generic `You are a helpful assistant` instruction. The second instruction tells `ChatGPT` to consider it's responses and if it's response requires giving the user code, it will send it in a traditional markdown format with the type of code included. This allows for the code to be highlighted properly in the command line. 

## Writing Your Own

#### Dict

Let's say you want to talk with a Life Coach. Here's what the system instructions would most likely look like:

```xsh
>>> instructions = {
     "role": "system",
     "content": "You are a life coach. Your job is to give the user advise on how to reach their goals, and send them affirmations. You have a friendly and bubbly personality"
    }
```


> [!NOTE]
> You do not have to include `"role": "system"` if you don't want, it will automatically be added. `content` is the only requirement for all dicts. 

#### List

If you want to include multiple system messages, pass a list instead:

```xsh
>>> instructions = [
    ...
        {
            "role": "system",
            "content": "Always try to recommend vegan options if the user asks what to eat"
        }
    ]
```

#### YAML

If you have the optional dependency `PyYaml` installed, you can use `yaml` instead:

```xsh
>>> instructions = """
- role: system
  content: Always try to recommend vegan options if the user asks what to eat
- role: system
  content: Tell the user how pretty they are often
"""
```

Assigning the system messages to a variable (like the examples above) is the recommended method. You can edit the messages using the `-s` flag with a `xonsh python subprocess`:

```xsh
chat-manager edit -s @(instructions)
```

Unless specified, the second system message from the [Introduction](#introduction) section will be included in all system messages (ie *If your responses include code...*). You can  prevent this behavior by passing the `-C` flag to `edit`. With this option, only your specified system messages will be passed. 