# flake8: noqa: E501 (line too long, conflicts with black on long multiline strings)
"""Script to export all guild members and their roles to per-guild .csv files."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import textwrap
from typing import Annotated, Any, Literal

import discord
from discord.ext.commands import Bot
from pydantic import AfterValidator, BaseModel, Field, model_validator

if sys.version_info >= (3, 11):
    from typing import Self, assert_never
else:
    from typing_extensions import Self, assert_never

logger = logging.getLogger(__name__)

DESCRIPTION = """\
Configure the EuroPython Discord guild.

Requires the environment variable 'BOT_TOKEN' to be set.
Requires bot privileges for receiving 'GUILD_MEMBER' events.

It will:
- Enable 'Community Server' features
- Configure system channels
- Create missing roles
    - Update colors
    - Update 'hoist' status
    - Update 'mentionable' status
    - Update role permissions
- Create missing categories, text channels, forums
    - Update positions
    - Update topics
    - Add missing forum tags
    - Update 'mandatory/optional' state of forum tags

To do manually:
- Configure role order

It will not:
- Delete roles
- Delete categories
- Delete channels
- Delete forum tags
"""

MultilineString = Annotated[
    str,
    AfterValidator(lambda text: textwrap.dedent(text.strip("\r\n").rstrip())),
]

BLUE = "#0096C7"
LIGHT_BLUE = "#8FD3E0"
DARK_ORANGE = "#E6412C"
ORANGE = "#E85D04"
YELLOW = "#FFD700"
PURPLE = "#D34EA5"
GREY = "#99AAB5"


Permission = Literal[
    "view_channel",
    "change_nickname",
    "send_messages",
    "send_messages_in_threads",
    "embed_links",
    "add_reactions",
    "use_external_emojis",
    "use_external_stickers",
    "read_message_history",
    "create_polls",
    "use_application_commands",
    "use_external_apps",
    "attach_files",
    "mention_everyone",
    "manage_messages",
    "manage_threads",
    "moderate_members",
    "manage_nicknames",
    "kick_members",
    "ban_members",
    "administrator",
]


class PermissionOverwrite(BaseModel):
    role: str
    allow: list[Permission] = Field(default_factory=list)
    deny: list[Permission] = Field(default_factory=list)


class Role(BaseModel):
    name: str
    color: str = Field(default=GREY, pattern="#[0-9A-F]{6}")
    hoist: bool = False
    mentionable: bool = False
    permissions: list[Permission] = Field(default_factory=list)


class ForumChannel(BaseModel):
    type: Literal["forum"] = "forum"

    name: str
    topic: MultilineString
    tags: list[str] = Field(default_factory=list)
    require_tags: bool = False
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)


class TextChannel(BaseModel):
    type: Literal["text"] = "text"

    name: str
    topic: MultilineString
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)


class Category(BaseModel):
    name: str
    channels: list[TextChannel | ForumChannel] = Field(discriminator="type")
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)


class GuildConfig(BaseModel):
    roles: list[Role]
    rules_channel_name: str
    system_channel_name: str
    public_updates_channel_name: str
    categories: list[Category]

    @model_validator(mode='after')
    def verify_system_channel_names(self) -> Self:
        channel_names = []
        for category in self.categories:
            for channel in category.channels:
                channel_names.append(channel.name)

        missing_channels = []
        for name in [self.rules_channel_name, self.system_channel_name, self.public_updates_channel_name]:
            if name not in channel_names:
                missing_channels.append(name)

        if missing_channels:
            raise ValueError(f"Missing system channels: {missing_channels}")

        return self


config = GuildConfig(
    roles=[
        Role(
            name="Admin",
            color=GREY,
            permissions=["administrator"],
        ),
        Role(
            name="Code of Conduct Committee",
            color=DARK_ORANGE,
            hoist=True,
            mentionable=True,
            permissions=["kick_members", "ban_members"],
        ),
        Role(
            name="Moderators",
            color=ORANGE,
            hoist=True,
            mentionable=True,
            permissions=[
                "manage_nicknames",
                "moderate_members",
                "manage_messages",
                "manage_threads",
            ],
        ),
        Role(
            name="Organizers", color=ORANGE, permissions=["mention_everyone", "use_external_apps"]
        ),
        Role(
            name="Volunteers",
            color=YELLOW,
            hoist=True,
            mentionable=True,
        ),
        Role(name="Onsite Volunteers"),
        Role(name="Remote Volunteers"),
        Role(
            name="Speakers",
            color=BLUE,
            hoist=True,
            mentionable=True,
        ),
        Role(
            name="Sponsors",
            color=LIGHT_BLUE,
            hoist=True,
            mentionable=True,
        ),
        Role(name="OSS"),
        Role(
            name="Participants",
            color=PURPLE,
            hoist=True,
            mentionable=True,
            permissions=["use_external_emojis", "use_external_stickers", "create_polls"],
        ),
        Role(name="Onsite Participants"),
        Role(name="Remote Participants"),
        Role(name="Programme Team"),
        Role(
            name="@everyone",
            permissions=[
                "view_channel",
                "change_nickname",
                "send_messages",
                "send_messages_in_threads",
                "embed_links",
                "add_reactions",
                "read_message_history",
                "use_application_commands",
            ],
        ),
    ],
    rules_channel_name="rules",
    system_channel_name="system-events",
    public_updates_channel_name="discord-updates",
    categories=[
        Category(
            name="Information",
            channels=[
                TextChannel(
                    name="rules",
                    topic="Please read the rules carefully!",
                ),
                TextChannel(
                    name="code-of-conduct",
                    topic="https://www.europython-society.org/coc/",
                ),
            ],
            permission_overwrites=[
                PermissionOverwrite(
                    role="@everyone",
                    deny=["send_messages"],
                )
            ]
        ),
        Category(
            name="EuroPython 2025",
            channels=[
                TextChannel(
                    name="announcements",
                    topic="Organisers will make EuroPython announcements in this channel",
                ),
                TextChannel(
                    name="general-chat",
                    topic="Social chat for conference participants. Please follow the Rules and Code of Conduct.",
                ),
                ForumChannel(
                    name="support",
                    topic="""
                        Use this forum channel to create support tickets if you **need support from the conference organization**. Please don't open forum threads related to other topics, as that makes it difficult for the organizers to keep track of support tickets that need their attention.

                        If you to make a report to the Code of Conduct Committee, please use coc@europython.eu or contact an organizer at the conference.
                        """,
                    tags=["Remote Support", "On-Site Support"],
                    require_tags=True,
                ),
                TextChannel(
                    name="introduction",
                    topic="Feel free to introduce yourself here :)",
                ),
                ForumChannel(
                    name="topics-and-interests",
                    topic="""
                        You can use this forum channel to start conversations focused around specific topics and interests, including topics unrelated to EuroPython 2024 or Python. Think of it like a virtual hallway track where you can discuss topics with the people you meet while participating in a conference.

                        **Use a descriptive title** that clearly highlights the topic you intend to discuss within this channel. However, do **keep in mind that conversations tend to meander away from their initial topic over time**. While it's okay to nudge the conversation back onto its original topic, do **be patient and civil** with each other, even if you perceive someone as going "off-topic".

                        Thank you for your cooperation in maintaining an open and welcoming environment for everyone!
                        """,
                ),
                ForumChannel(
                    name="social-activities",
                    topic="""
                        # Social Activities organized by and for attendees
                        You can use this channel to organize a social activity with other attendees of the conference. Do note that EuroPython only provides a space for attendees to coordinate social activities, it does not officially endorse activities posted here.

                        ## topic for a good post
                        - Use a **descriptive title** that captures the core of your activity
                        - If relevant, **include the date and time in your title**
                        - Indicate if your activity is **in-person** or **remote** by selecting the appropriate tag
                        """,
                    tags=["In Person", "Remote"],
                    require_tags=True,
                ),
                TextChannel(
                    name="lost-and-found",
                    topic="Channel for the coordination of lost and found items. Please bring found items to the registration desk.",
                ),
            ],
        ),
        Category(
            name="Rooms",
            channels=[
                TextChannel(
                    name="programme-notifications",
                    topic="Find the latest information about starting sessions here!",
                ),
                TextChannel(name="forum-hall", topic="Livestream: [TBA]"),
                TextChannel(name="south-hall-2a", topic="Livestream: [TBA]"),
                TextChannel(name="south-hall-2b", topic="Livestream: [TBA]"),
                TextChannel(name="north-hall", topic="Livestream: [TBA]"),
                TextChannel(name="terrace-2a", topic="Livestream: [TBA]"),
                TextChannel(name="terrace-2b", topic="Livestream: [TBA]"),
                TextChannel(
                    name="exhibit-hall", topic="For conversations related to the exhibit hall."
                ),
                TextChannel(
                    name="open-space",
                    topic="For conversations related to the open spaces. We'll also post photos of the open space session board here!",
                ),
                ForumChannel(
                    name="tutorials",
                    topic="""
                        We kindly ask you to **only create one thread per tutorial**. Having too many threads makes it more difficult for participants to find the thread of the tutorial they're participating in.

                        **Tips:**
                        - On desktop, you can open a forum thread in "full window mode" using the `...` option menu in the top bar.
                        - If you select to "follow" a thread, it will appear directly in your channel list.
                        """,
                ),
                ForumChannel(
                    name="sprints",
                    topic="To keep things manageable, I think one post/thread per sprint would be the best. If there are reasons to create multiple threads/posts (e.g., for groups working on a sub-project), that should be fine, too.",
                ),
                ForumChannel(
                    name="slides-and-artefacts",
                    topic="""
                        You can create a thread for your talk where you can add slides and other artefacts.

                        - Please add the **title of your talk **and the **names of the speakers** in the title. This makes it easy for participants to find your talk.
                        - Only create a single post per talk!
                        - Participants can't send messages in the thread.
                        """,
                ),
            ],
        ),
        Category(
            name="Conference Organization",
            channels=[
                TextChannel(
                    name="announcements-volunteers",
                    topic="Announcements for conference volunteers",
                ),
                TextChannel(
                    name="conference-discussion",
                    topic="For on-topic conversations related to organizing EuroPython 2024. Please use #volunteers-lounge for off-topic conversations!",
                ),
                TextChannel(
                    name="volunteers-lounge",
                    topic="Social chat for volunteers. Please follow the #rules and #code-of-conduct!",
                ),
                TextChannel(
                    name="sponsors-lounge",
                    topic="Social chat for sponsors. Please follow the #rules and #code-of-conduct!",
                ),
                TextChannel(
                    name="speakers-lounge",
                    topic="SChannel open to all speakers & conference volunteers. Please follow the #rules and #code-of-conduct!",
                ),
                TextChannel(
                    name="oss-lounge",
                    topic="Please follow the #rules and #code-of-conduct!",
                ),
                TextChannel(
                    name="moderators",
                    topic="For discussions related to ongoing moderation activities, moderation policy, and other moderation-related topic.",
                ),
                TextChannel(
                    name="discord-updates",
                    topic="Discord will send community server notifications here.",
                ),
            ],
        ),
        Category(
            name="Sponsors",
            channels=[
                ForumChannel(
                    name="job-board",
                    topic="""
                        Make sure your job openings follows the following rules:

                        1. Title: A clear and concise title including the role and the Company/Organization
                        2. Job Type: Indicate whether the job is full-time, part-time, contract-based, freelance, or an internship.
                        3. Job Description: Provide a URL or text explaining the job.
                        4. Application Deadline: If there is a specific deadline for applications, mention it in the post.
                        5. Salary/Compensation: If possible and appropriate, include salary or compensation details.
                        6. Additional Information: stuff like:  perks, or notable company culture, include them in the post.
                        7. Relevant Tags: Use relevant tags or keywords to categorize the job post. Please let us know if important tags are missing.
                        8. No Discrimination: Ensure that the job post does not include any discriminatory language or requirements.
                        9. Updates and Removal: If the job position is filled or no longer available, update or remove the post to avoid confusion for job seekers.
                        """,
                    tags=[
                        "Remote",
                        "Hybrid",
                        "On-site",
                        "AI",
                        "Data Science",
                        "Data Engineering",
                        "Backend",
                        "Frontend",
                        "Full Stack",
                        "Cloud",
                        "Web",
                        "DevOps",
                        "Junior",
                        "Professional",
                        "Senior",
                    ],
                    require_tags=True,
                ),
                TextChannel(
                    name="example-sponsor", topic="This is how a sponsor channel could look like"
                ),
            ],
        ),
        Category(
            name="Registration",
            channels=[
                TextChannel(name="welcome", topic="Welcome to our server, please register."),
                TextChannel(
                    name="registration", topic="Please follow the registration instructions."
                ),
                ForumChannel(
                    name="registration-help",
                    topic="""
                        # This channel is only for asking for help with registration, not for general discussion.

                        As this community is only intended for EuroPython participants, there are no public discussion channels.
                        """,
                ),
                TextChannel(
                    name="registration-log",
                    topic="The EuroPython bot will log registration actions here to help us with debugging.",
                ),
                TextChannel(
                    name="system-events",
                    topic='This channel will show "raw" joins to keep track of who joins and who registered without hdiving into the audit log.',
                ),
            ],
        ),
    ],
)


def report_error(message: str) -> None:
    """Print an error message to stderr."""
    print("ERROR:", message, file=sys.stderr)


async def configure_category(
    guild: discord.Guild, template: Category, position: int
) -> discord.CategoryChannel:
    logger.info("Configure category %s at position %d", template.name, position)
    for category in guild.categories:
        if category.name == template.name:
            logger.debug("Found category")
            if category.position != position:
                logger.debug("Update position")
                await category.edit(position=position)
            return category

    logger.debug("Create category")
    return await guild.create_category(template.name, position=position)


async def configure_text_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel | None,
    template: TextChannel,
    position: int,
) -> discord.TextChannel:
    logger.info("Configure text channel %s at position %d", template.name, position)
    for channel in guild.text_channels:
        if channel.name == template.name:
            logger.debug("Found text channel")
            if channel.category != category:
                logger.debug("Update category")
                await channel.edit(category=category)
            if channel.position != position:
                logger.debug("Update position")
                await channel.edit(position=position)
            if channel.topic != template.topic:
                logger.debug("Update topic")
                await channel.edit(topic=template.topic)
            return channel

    logger.debug("Create text channel", template.name)
    return await guild.create_text_channel(
        template.name, category=category, topic=template.topic, position=position
    )


async def configure_tags(
    channel: discord.ForumChannel, expected_tags: list[str], *, required: bool
) -> None:
    logger.info("Configure tags %s for channel %s", channel.name, channel.name)
    existing_tags = {tag.name: tag for tag in channel.available_tags}
    tags_to_create = set(expected_tags) - set(existing_tags)

    if tags_to_create:
        for tag_name in tags_to_create:
            logger.debug("Create tag %s", tag_name)
            existing_tags[tag_name] = await channel.create_tag(name=tag_name)

        logger.debug("Update available tags for channel %s", channel.name)
        await channel.edit(available_tags=(list(existing_tags.values())))

    if required and not channel.flags.require_tag:
        await channel.edit(require_tag=required)


async def configure_forum_channel(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    template: ForumChannel,
    position: int,
) -> discord.ForumChannel:
    logger.info("Configure forum channel %s at position %d", template.name, position)
    for channel in guild.forums:
        if channel.name == template.name:
            if channel.category is None or channel.category != category:
                logger.debug("Update category")
                await channel.edit(category=category)
            if channel.position != position:
                logger.debug("Update position")
                await channel.edit(position=position)
            if channel.topic != template.topic:
                logger.debug("Update topic")
                await channel.edit(topic=template.topic)

            await configure_tags(channel, template.tags, required=template.require_tags)
            return channel

    logger.debug("Create forum channel %s", template.name)
    channel = await guild.create_forum(
        template.name, category=category, topic=template.topic, position=position
    )
    await configure_tags(channel, template.tags, required=template.require_tags)

    return channel


def create_permissions(permissions: list[Permission]) -> discord.Permissions:
    return discord.Permissions(**{perm: True for perm in permissions})


async def configure_role(guild: discord.Guild, template: Role) -> discord.Role:
    logger.info("Configure role %s", template.name)
    for role in guild.roles:
        if role.name == template.name:
            logger.debug("Found role")
            if role.colour != template.color:
                logger.debug("Update color")
                await role.edit(colour=discord.Color.from_str(template.color))
            if role.hoist != template.hoist:
                logger.debug("Update hoist")
                await role.edit(hoist=template.hoist)
            if role.mentionable != template.mentionable:
                logger.debug("Update mentionable")
                await role.edit(mentionable=template.mentionable)
            permissions = create_permissions(template.permissions)
            if role.permissions != permissions:
                logger.debug("Update permissions")
                await role.edit(permissions=permissions)
            return role

    logger.debug("Create role %s", template.name)
    return await guild.create_role(
        name=template.name,
        colour=discord.Color.from_str(template.color),
        hoist=template.hoist,
        mentionable=template.mentionable,
        permissions=create_permissions(template.permissions),
    )


async def configure_guild(guild: discord.Guild, template: GuildConfig) -> None:
    logger.info("Configuring roles")
    for role_template in template.roles:
        await configure_role(guild, role_template)

    # turn guild into community server
    if "COMMUNITY" not in guild.features:
        logger.info("Enabling community server features")

        # create required channels (will be positioned later)
        channels_by_name = {}
        for category_template in template.categories:
            for channel_template in category_template.channels:
                if channel_template.name in [
                    template.rules_channel_name,
                    template.public_updates_channel_name,
                ]:
                    logger.debug("Creating required channel %s", channel_template.name)
                    text_channel = await configure_text_channel(
                        guild, category=None, template=channel_template, position=0
                    )
                    channels_by_name[channel_template.name] = text_channel

        logger.debug("Raising verification level to medium")
        if guild.verification_level < discord.VerificationLevel.medium:
            await guild.edit(verification_level=discord.VerificationLevel.medium)

        logger.debug("Enabling guild 'COMMUNITY' feature")
        await guild.edit(
            community=True,
            rules_channel=channels_by_name[template.rules_channel_name],
            public_updates_channel=channels_by_name[template.public_updates_channel_name],
            explicit_content_filter=discord.ContentFilter.all_members,
        )

    # create channels
    logger.info("Creating channels")
    channel_position = 0
    category_position = 0
    channels_by_name = {}
    for category_template in template.categories:
        d_category = await configure_category(guild, category_template, category_position)
        for channel_template in category_template.channels:
            if isinstance(channel_template, TextChannel):
                channel = await configure_text_channel(
                    guild, d_category, channel_template, channel_position
                )
            elif isinstance(channel_template, ForumChannel):
                channel = await configure_forum_channel(
                    guild, d_category, channel_template, channel_position
                )
            else:
                assert_never(channel_template)
            channels_by_name[channel_template.name] = channel
            channel_position += 1
        category_position += 1

    # Configure system channels and events
    logger.info("Configuring system channels and events")
    if guild.system_channel is None or guild.system_channel.name != template.system_channel_name:
        logger.debug("Update system channel")
        await guild.edit(system_channel=channels_by_name[template.system_channel_name])
    if guild.public_updates_channel.name != template.public_updates_channel_name:
        logger.debug("Update public updates channel")
        await guild.edit(
            public_updates_channel=channels_by_name[template.public_updates_channel_name]
        )
    if guild.system_channel.name != template.rules_channel_name:
        logger.debug("Update rules channel")
        await guild.edit(rules_channel=channels_by_name[template.rules_channel_name])
    logger.debug("Set system channel flags")
    await guild.edit(
        system_channel_flags=discord.SystemChannelFlags(
            join_notifications=True,
            join_notification_replies=False,
            guild_reminder_notifications=False,
        )
    )


class GuildConfigurationBot(Bot):
    def __init__(self) -> None:
        """Discord bot which exports all guild members to .csv files and then stops itself."""
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix="$",
        )

    async def on_ready(self) -> None:
        """Event handler for successful connection."""
        for guild in self.guilds:
            await configure_guild(guild, config)

        await self.close()

    async def on_error(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        """Event handler for uncaught exceptions."""
        exc_type, exc_value, _exc_traceback = sys.exc_info()
        if exc_type is None:
            report_error(f"Unknown error during {event}(*{args}, **{kwargs})")
        else:
            report_error(f"{exc_type.__name__} {exc_value}")

        # let discord.py log the exception
        await super().on_error(event, *args, **kwargs)

        await self.close()


async def run_bot(bot: Bot, token: str) -> None:
    """Run a Discord bot."""
    async with bot as _bot:
        try:
            await _bot.login(token)
            await _bot.connect()
        except discord.LoginFailure:
            report_error("Invalid Discord bot token")
        except discord.PrivilegedIntentsRequired:
            report_error("Insufficient privileges. Required events: 'GUILD_MEMBERS'")


def main() -> None:
    """Run this application."""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--verbose", action="store_true", help="Enable INFO logging")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")
    args = parser.parse_args()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token is None:
        raise RuntimeError("'BOT_TOKEN' environment variable is not set")

    if args.verbose:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    bot = GuildConfigurationBot()
    asyncio.run(run_bot(bot, bot_token))


if __name__ == "__main__":
    main()
