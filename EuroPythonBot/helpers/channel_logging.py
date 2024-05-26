from discord import Member, TextChannel


async def log_to_channel(channel: TextChannel, user: Member, name="", order="", roles=tuple(), error=None):
    if error is None:
        content = f"✅ : **<@{user.id}> REGISTERED**\n{name=} {order=} {roles=}\n"
    else:
        error_name = error.__class__.__name__
        content = f"❌ : **<@{user.id}> encountered an ERROR**\n{error_name}: {error}\n"

    await channel.send(content=content)
