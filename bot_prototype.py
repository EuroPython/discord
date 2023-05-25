import discord
from discord.errors import Forbidden

from pretix_connector import (
    TicketRole,
    TicketValidationError,
    get_ticket_roles_from_message_with_ticket_id,
)
from question_handling import message_is_question, handle_question
from settings import BOT_TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)
# the line below is a test of storing globals in the client object.
# it seems that you can access the client from the message
# like this "message._state._get_client()"
client.my_global_greeting = "Hey"


@client.event
async def on_ready():
    print("Bot is ready.")
    # TODO - set rights for pinning!
    # TODO - prototype pinned message change
    channel = discord.utils.get(client.get_all_channels(), name="general")
    try:
        message = await channel.send("This is a pinned message - the bot is ready!")
        await message.pin()
    except Forbidden as e:
        print(e)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # different channels need different behaviour.
    # for now just channels one room

    if message.channel.name == "general":

        # debug via print
        print(f"Message from {message.author}: {message.content}")
        print(f"Guild {message.guild.name}")
        print(f"{message.author.display_name=}")

        content = message.content

        global_greeting = "Howdy"
        if message.guild is not None:
            # if you don't have the client, access it this way
            # global_greeting = message._state._get_client().my_global_greeting
            global_greeting = client.my_global_greeting

        # just echo something
        await message.channel.send(
            f"{global_greeting}, {message.author.mention}! I understood '{content}'"
        )

        # make questions votable
        # for rooms that allow questions, of course.
        if await message_is_question(content=content):
            await handle_question(message=message)
            return

        # test to init a private CoC chat
        if content:
            if "coc" in content.lower():
                try:
                    # Try to send a private message
                    await message.author.send("Do you need CoC help?")
                except Forbidden:
                    print(
                        f"Could not send a DM to {message.author}. They may have blocked DMs."
                    )
                try:
                    # for security reason, maybe delete this?
                    await message.delete()
                except Forbidden:
                    print(f"Could not remove coc message.")

        # assign role

        # Check if user has the role, assign if not
        # Get the role to assign
        # TODO - validate if role should be assigned.
        # 1 - check if role is assigned
        # 2 - if not - parse question for ticket ID and call validation

        # "role": This here should be done on startup!
        # There should also be more
        role = discord.utils.get(message.guild.roles, name="new role")

        if role not in message.author.roles:
            try:
                user_roles = get_ticket_roles_from_message_with_ticket_id(
                    message=content, screen_name=message.author
                )
                if user_roles:
                    if TicketRole.ATTENDENT in user_roles:
                        await message.author.add_roles(role)
                        await message.channel.send(
                            f"You have been assigned attendent roles"
                        )
                else:
                    await message.channel.send(
                        f"Please reply with your ticket code (example V001, S001, etc..)"
                    )
            except TicketValidationError as e:
                await message.channel.send(
                    f"There has been a problem with your ticket code. {e}"
                )


@client.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    if before.content != after.content:
        print(
            f"Message from {before.author} edited from {before.content} to {after.content}"
        )

    if message_is_question(before.content) or message_is_question(after.content):
        # TODO - if this message is a question we need to decide on behaviour.
        # we can't prevent this but may reset the vote
        # also we need to do something about messages that become a question or
        # lose questions later.
        pass


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
