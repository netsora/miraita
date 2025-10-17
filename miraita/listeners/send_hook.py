from arclet.entari import MessageChain, Plugin, Session

plugin = Plugin.current()


@plugin.use("::before_send")
async def send_hook(
    message: MessageChain, session: Session | None = None
) -> MessageChain:
    if session is None:
        return message

    at, reply = session._resolve(True, True)

    if at:
        message.insert(0, at)
    if reply:
        message.insert(0, reply)

    return message
