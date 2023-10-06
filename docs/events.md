# Events

**NEW in Version 0.1.3**

Three new events are added to `xonsh` events which help notify `chat-manager` when a change has been made in the current namespace related to chats.

### *on_chat_create(inst: ChatGPT) -> None*
Fired when new chat is created. Passes the new instance to be added to the chat manager.

### *on_chat_destroy(inst: ChatGPT) -> None*
Fired when chat is destroyed. Passes the instance to be removed from the chat manager.

### *on_chat_used(inst: ChatGPT) -> None*
Fires when chat is used, i.e. chatgpt is called. Passes the instance of the chat instance to update the current chat for the manager.