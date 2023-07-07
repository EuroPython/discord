async def log_to_channel(channel, interaction, error=None):
    user = interaction.user
    if user_name := user.nick is None:
        user_name = user.name

    if error is None:
        content = f"✅ : **`{user_name}` REGISTERED**\nas {[role.name for role in user.roles[1:]]}\n"
    else:
        content = f"❌ : **`{user_name}` encounter an ERROR**\n{error.__class__.__name__}: {error}\n"

    await channel.send(content=content)
