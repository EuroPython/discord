import discord

from settings import BOT_TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("Bot is ready.")
    # TODO - set rights for pinning!
    # TODO - prototype pinned message change
    channel = discord.utils.get(client.get_all_channels(), name="general")
    message = await channel.send("This is a pinned message - the bot is ready!")
    await message.pin()


@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.name == "general":
        print(f"Message from {message.author}: {message.content}")
        print(f"Guild {message.guild.name}")
        print(f"{message.author.display_name=}")
        content = message.content

        await message.channel.send(
            f"Hello, {message.author.mention}! I understood {content}"
        )

        # make questions votable
        if content:
            if any(
                (
                    content.lower().startswith("q:"),
                    content.lower().startswith("question"),
                )
            ):
                await message.add_reaction("0️⃣")
                await message.channel.send(
                    f"Thanks for the question, please vote for it"
                )

        # Check if user has the role, assign if not
        # Get the role to assign
        # TODO - validate if role should be assigned.
        # 1 - check if role is assigned
        # 2 - if not - parse question for ticket ID and call validation
        # "role": This here should be done on startup!
        role = discord.utils.get(message.guild.roles, name="new role")
        if role not in message.author.roles:
            await message.author.add_roles(role)


@client.event
async def on_reaction_add(reaction, user):
    # TODO limit to allowed reactions (for example on questions)
    if user.bot:
        return
    print(
        f"{user} has added {reaction.emoji} to a message with content: {reaction.message.content}"
    )


@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return
    print(
        f"{user} has removed {reaction.emoji} from a message with content: {reaction.message.content}"
    )


# note: raw reactions are to messages existing before the bot's last restart
@client.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return
    channel = client.get_channel(payload.channel_id)  # Get the channel
    message = await channel.fetch_message(payload.message_id)  # Get the message
    print(
        f"{payload.member} has added {payload.emoji} to a message with content: {message.content}"
    )


# note: raw reactions are to messages existing before the bot's last restart
@client.event
async def on_raw_reaction_remove(payload):
    channel = client.get_channel(payload.channel_id)  # Get the channel
    message = await channel.fetch_message(payload.message_id)  # Get the message
    print(f"A reaction has been removed from a message with content: {message.content}")


if __name__ == "__main__":
    client.run(BOT_TOKEN)
