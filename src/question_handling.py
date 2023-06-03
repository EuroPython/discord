from typing import Optional

import discord


async def message_is_question(content: Optional[str]) -> bool:
    if content is None:
        return False

    if any(
        (
            content.lower().startswith("q:"),
            content.lower().startswith("question"),
        )
    ):
        return True
    return False


async def handle_question(
    message: discord.Message, before_message: Optional[discord.Message] = None
) -> None:
    # the bot tracks the questions
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
    # TODO - limit the character length of questions
    # TODO - editing!

    await message.add_reaction("0️⃣")
    await message.channel.send(
        "Thanks for the question, other people - please vote for it"
    )
