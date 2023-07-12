async def log_to_channel(channel, interaction, name="", order="", roles=tuple(), error=None):
    user = interaction.user
    if user.nick is None:
        user_name = user.name
    else:
        user_name = user.nick

    if error is None:
        content = f"✅ : **`{user_name}` REGISTERED**\n{name=} {order=} {roles=}\n"
    else:
        content = f"❌ : **`{user_name}` encounter an ERROR**\n{error.__class__.__name__}: {error}\n"

    await channel.send(content=content)
