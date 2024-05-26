async def log_to_channel(channel, interaction, name="", order="", roles=tuple(), error=None):
    user = interaction.user
    if user.nick is None:
        user_name = user.name
    else:
        user_name = user.nick

    user_identifier = f"{user_name} ({user.id})"
    if error is None:
        content = f"✅ : **`{user_identifier}` REGISTERED**\n{name=} {order=} {roles=}\n"
    else:
        error_name = error.__class__.__name__
        content = f"❌ : **`{user_identifier}` encountered an ERROR**\n{error_name}: {error}\n"

    await channel.send(content=content)
