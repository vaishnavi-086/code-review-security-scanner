from datetime import datetime
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from protocols import handle_review_request

agent = Agent()

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def on_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    text = msg.text()
    if not text:
        return
    reply = await handle_review_request(ctx, sender, text)
    content = [TextContent(type="text", text=reply)]
    await ctx.send(sender, ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content))


@protocol.on_message(ChatAcknowledgement)
async def on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
