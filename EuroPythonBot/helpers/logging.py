async def log_to_channel(channel, interaction, error=None):
    if user_name := interaction.user.nick is None:
        user_name = interaction.user.name

    if error is None:
        content = f"✅ : `{user_name}` registered"
    else:
        content = f"❌ : `{user_name}` encounter an error - {error.__class__.__name__}: {error}"

    await channel.send(content=content)
