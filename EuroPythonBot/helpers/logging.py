async def log_to_channel(channel, interaction, error=None):
    user = interaction.user
    if user_name := user.nick is None:
        user_name = user.name

    if error is None:
        content = f"✅ : `{user_name}` registered as {[role.name for role in user.roles[1:]]}"
    else:
        content = f"❌ : `{user_name}` encounter an error - {error.__class__.__name__}: {error}"

    await channel.send(content=content)
