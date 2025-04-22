"""Channel logging."""


async def log_to_channel(channel, interaction, name="", order="", roles=(), error=None) -> None:  # noqa: ANN001, PLR0913
    """Log to channel."""
    user = interaction.user
    user_name = user.name if user.nick is None else user.nick

    user_identifier = f"{user_name} ({user.id})"
    if error is None:
        content = f"✅ : **`{user_identifier}` REGISTERED**\n{name=} {order=} {roles=}\n"
    else:
        error_name = error.__class__.__name__
        content = f"❌ : **`{user_identifier}` encounter an ERROR**\n{error_name}: {error}\n"

    await channel.send(content=content)
