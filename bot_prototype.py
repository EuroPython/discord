import discord

from pretix_connector import (
    get_ticket_roles_from_message_with_ticket_id,
    TicketRole,
    TicketValidationError,
)
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

    # different channels need different behaviour.
    # for now just channels one room

    if message.channel.name == "general":

        # debug via print
        print(f"Message from {message.author}: {message.content}")
        print(f"Guild {message.guild.name}")
        print(f"{message.author.display_name=}")

        content = message.content

        # just echo something
        await message.channel.send(
            f"Hello, {message.author.mention}! I understood '{content}'"
        )

        # make questions votable
        # for rooms that allow questions, of course.
        if content:
            if any(
                (
                    content.lower().startswith("q:"),
                    content.lower().startswith("question"),
                )
            ):
                # in each of these the bot tracks the questions
                # and provides a secret interface for the session host to
                # read them
                # there will also be a feature that resets the question,
                # the votes will stay. but it will no longer show up for the
                # session host. Including a feature to reset all questions at the
                # start of the next session

                # my plan is to use a local sqlite3 database to persist this info
                # to make it survive restarts
                # for now, just tack on a voting icon

                # TODO - prevent voting for your own question!!!

                await message.add_reaction("0️⃣")
                await message.channel.send(
                    f"Thanks for the question, other people - please vote for it"
                )


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
