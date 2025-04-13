# flake8: noqa: E501 (line too long, conflicts with black on long multiline strings)
"""Script to export all guild members and their roles to per-guild .csv files."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import textwrap
from collections import defaultdict
from typing import Annotated, Any, Literal

import discord
from discord.ext.commands import Bot
from discord.utils import get as discord_get
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
- Update roles
    - Add missing roles
    - Update colors
    - Update 'hoist' flag
    - Update 'mentionable' flag
    - Update role permissions
- Update categories, text channels, and forums
    - Add missing categories, text channels, and forums
    - Update positions
    - Add missing forum tags
    - Update 'mandatory/optional' state of forum tags
    - Update category, text channel, and forum permission overwrites
- Update category and channel permission overwrites

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
    "create_public_threads",
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
    "manage_channels",
    "moderate_members",
    "manage_nicknames",
    "kick_members",
    "ban_members",
    "administrator",
]


class PermissionOverwrite(BaseModel):
    roles: list[str]
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
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)
    require_tag: bool = False


class TextChannel(BaseModel):
    type: Literal["text"] = "text"

    name: str
    topic: MultilineString
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)

    default_messages: list[MultilineString] = Field(default_factory=list)


class Category(BaseModel):
    name: str
    channels: list[TextChannel | ForumChannel] = Field(discriminator="type")
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)


class GuildConfig(BaseModel):
    roles: list[Role]
    rules_channel_name: str
    system_channel_name: str
    updates_channel_name: str
    categories: list[Category]

    @model_validator(mode="after")
    def verify_system_channel_names(self) -> Self:
        channel_names = []
        for category in self.categories:
            for channel in category.channels:
                channel_names.append(channel.name)

        missing_channels = []
        for name in [
            self.rules_channel_name,
            self.system_channel_name,
            self.updates_channel_name,
        ]:
            if name not in channel_names:
                missing_channels.append(name)

        if missing_channels:
            raise ValueError(f"Missing system channels: {missing_channels}")

        return self

    @model_validator(mode="after")
    def verify_permission_roles(self) -> Self:
        roles = [role.name for role in self.roles]

        missing_roles = set()
        for category in self.categories:
            for overwrite in category.permission_overwrites:
                for role in overwrite.roles:
                    if role not in roles:
                        missing_roles.add(role)
            for channel in category.channels:
                for overwrite in channel.permission_overwrites:
                    for role in overwrite.roles:
                        if role not in roles:
                            missing_roles.add(role)

        if missing_roles:
            raise ValueError(f"Missing roles: {missing_roles}")

        return self


ROLE_COC = "Code of Conduct Committee"
ROLE_MODERATORS = "Moderators"
ROLE_ORGANIZERS = "Organizers"
ROLE_VOLUNTEERS = "Volunteers"
ROLE_SPEAKERS = "Speakers"
ROLE_SPONSORS = "Sponsors"
ROLE_PARTICIPANTS = "Participants"
ROLE_EVERYONE = "@everyone"

ROLES_COC = [ROLE_COC]
ROLES_MODERATORS = [ROLE_MODERATORS, *ROLES_COC]
ROLES_ORGANIZERS = [ROLE_ORGANIZERS, *ROLES_MODERATORS]
ROLES_VOLUNTEERS = [ROLE_VOLUNTEERS, *ROLES_ORGANIZERS]
ROLES_SPEAKERS = [ROLE_SPEAKERS, *ROLES_ORGANIZERS]
ROLES_SPONSORS = [ROLE_SPONSORS, *ROLES_ORGANIZERS]
ROLES_REGISTERED = [ROLE_PARTICIPANTS, ROLE_SPONSORS, ROLE_SPEAKERS, *ROLES_VOLUNTEERS]

config = GuildConfig(
    roles=[
        Role(
            name="Admin",
            color=GREY,
            permissions=["administrator"],
        ),
        Role(
            name=ROLE_COC,
            color=DARK_ORANGE,
            hoist=True,
            mentionable=True,
            permissions=["kick_members", "ban_members"],
        ),
        Role(
            name=ROLE_MODERATORS,
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
            name=ROLE_ORGANIZERS,
            color=ORANGE,
            permissions=["mention_everyone", "use_external_apps"],
        ),
        Role(
            name=ROLE_VOLUNTEERS,
            color=YELLOW,
            hoist=True,
            mentionable=True,
        ),
        Role(name="Onsite Volunteers"),
        Role(name="Remote Volunteers"),
        Role(
            name=ROLE_SPEAKERS,
            color=BLUE,
            hoist=True,
            mentionable=True,
        ),
        Role(
            name=ROLE_SPONSORS,
            color=LIGHT_BLUE,
            hoist=True,
            mentionable=True,
        ),
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
                "create_public_threads",
                "embed_links",
                "add_reactions",
                "read_message_history",
                "use_application_commands",
            ],
        ),
    ],
    rules_channel_name="rules",
    system_channel_name="system-events",
    updates_channel_name="discord-updates",
    categories=[
        Category(
            name="Information",
            channels=[
                TextChannel(
                    name="rules",
                    topic="Please read the rules carefully!",
                    default_messages=[
                        """
                        ## Community Rules

                        **Rule 1**
                        Follow the [EuroPython Society Code of Conduct](https://www.europython-society.org/coc/).
                        **Rule 2**
                        Use English to the best of your ability. Be polite if someone speaks English imperfectly.
                        **Rule 3**
                        Use the name on your ticket as your display name. This will be done automatically during the #registration-form process.
                        
                        **Reporting Incidents**
                        If you notice something that needs the attention of a moderator of the community, please ping the <@&Moderators> role.
                        
                        Note that not all moderators are a member of the EuroPython Code of Conduct team. See the <#code-of-conduct> channel to read how you can report Code of Conduct incidents.
                        """
                    ],
                ),
                TextChannel(
                    name="code-of-conduct",
                    topic="https://www.europython-society.org/coc/",
                    default_messages=[
                        """
                        ## EuroPython Society Code of Conduct
                        EuroPython is a community conference intended for networking and collaboration in the developer community.
                        
                        We value the participation of each member of the Python community and want all participants to have an enjoyable and fulfilling experience. Accordingly, all attendees are expected to show respect and courtesy to other attendees throughout the conference and at all conference events.
                        
                        To make clear what is expected, all staff, attendees, speakers, exhibitors, organisers, and volunteers at any EuroPython event are required to conform to the [Code of Conduct](https://www.europython-society.org/coc/), as set forth by the [EuroPython Society](https://www.europython-society.org/about/). Organisers will enforce this code throughout the event.
                        
                        **Please read the Code of Conduct:** https://www.europython-society.org/coc/
                        """,
                        """
                        ## Reporting Incidents
                        **If you believe someone is in physical danger, including from themselves**, the most important thing is to get that person help. Please contact the appropriate crisis number, non-emergency number, or police number. If you are a EuroPython attendee, you can consult with a volunteer or organiser to help find an appropriate number.
                        
                        If you believe a [Code of Conduct](https://www.europython-society.org/coc/) incident has occurred, we encourage you to report it. If you are unsure whether the incident is a violation, or whether the space where it happened is covered by the Code of Conduct, we encourage you to still report it. We are fine with receiving reports where we decide to take no action for the sake of creating a safer space.
                        """
                        """
                        ## General Reporting Procedure
                        If you are being harassed, notice that someone else is being harassed, or have any other concerns, please contact a member of the Code of Conduct committee immediately. They can be reached by emailing **coc@europython.eu**.
                        
                        If you prefer, you can also directly contact:
                        
                        - Person 1
                          - Email: ...@europython.eu
                          - Telegram: @...
                          - Discord: <@...>
                        - Person 2
                          - Email: ...@europython.eu
                          - Telegram: @...
                          - Discord: <@...>
                        - Person 3
                          - Email: ...@europython.eu
                          - Discord: <@...>
                        - Person 4
                          - Email: ...@europython.eu
                          - Discord: <@...>
                        
                        Committee members have the role <@&Code of Conduct Committee> in this community.
                        """,
                        """
                        ## Links
                        - [EuroPython Society Code of Conduct](https://www.europython-society.org/coc/)
                        - [Incident Reporting Procedure](https://www.europython-society.org/coc-incident-reporting/)
                        - [Procedure for Incident Response](https://www.europython-society.org/coc-enforcement-procedure/)
                        """,
                    ],
                ),
            ],
            permission_overwrites=[
                PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["send_messages"])
            ],
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
                    require_tag=True,
                ),
                TextChannel(
                    name="introduction",
                    topic="Feel free to introduce yourself here :)",
                ),
                ForumChannel(
                    name="topics-and-interests",
                    topic="""
                        You can use this forum channel to start conversations focused around specific topics and interests, including topics unrelated to EuroPython or Python. Think of it like a virtual hallway track where you can discuss topics with the people you meet while participating in a conference.

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
                    require_tag=True,
                ),
                TextChannel(
                    name="lost-and-found",
                    topic="Channel for the coordination of lost and found items. Please bring found items to the registration desk.",
                ),
            ],
            permission_overwrites=[
                PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["view_channel"]),
                PermissionOverwrite(roles=ROLES_REGISTERED, allow=["view_channel"]),
            ],
        ),
        Category(
            name="Rooms",
            channels=[
                TextChannel(
                    name="programme-notifications",
                    topic="Find the latest information about starting sessions here!",
                    permission_overwrites=[
                        PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["send_messages"])
                    ],
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
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_REGISTERED,
                            deny=["create_public_threads"],
                        ),
                        PermissionOverwrite(
                            roles=ROLES_SPEAKERS,
                            allow=["create_public_threads"],
                        ),
                    ],
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
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_REGISTERED,
                            deny=["create_public_threads"],
                        ),
                        PermissionOverwrite(
                            roles=ROLES_SPEAKERS,
                            allow=["create_public_threads"],
                        ),
                    ],
                ),
            ],
            permission_overwrites=[
                PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["view_channel"]),
                PermissionOverwrite(roles=ROLES_REGISTERED, allow=["view_channel"]),
            ],
        ),
        Category(
            name="Conference Organization",
            channels=[
                TextChannel(
                    name="announcements-volunteers",
                    topic="Announcements for conference volunteers",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_VOLUNTEERS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="conference-discussion",
                    topic="For on-topic conversations related to organizing EuroPython. Please use #volunteers-lounge for off-topic conversations!",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_VOLUNTEERS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="volunteers-lounge",
                    topic="Social chat for volunteers. Please follow the #rules and #code-of-conduct!",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_VOLUNTEERS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="sponsors-lounge",
                    topic="Social chat for sponsors. Please follow the #rules and #code-of-conduct!",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_SPONSORS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="speakers-lounge",
                    topic="Channel open to all speakers & conference volunteers. Please follow the #rules and #code-of-conduct!",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_SPEAKERS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="moderators",
                    topic="For discussions related to ongoing moderation activities, moderation policy, and other moderation-related topic.",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=ROLES_MODERATORS,
                            allow=["view_channel"],
                        ),
                    ],
                ),
                TextChannel(
                    name="discord-updates",
                    topic="Discord will send community server notifications here.",
                ),
            ],
            permission_overwrites=[
                PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["view_channel"]),
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
                    require_tag=True,
                    permission_overwrites=[
                        PermissionOverwrite(roles=ROLES_REGISTERED, deny=["create_public_threads"]),
                        PermissionOverwrite(roles=ROLES_SPONSORS, allow=["create_public_threads"]),
                    ],
                ),
                TextChannel(
                    name="example-sponsor", topic="This is how a sponsor channel could look like"
                ),
            ],
        ),
        Category(
            name="Registration",
            channels=[
                TextChannel(
                    name="welcome",
                    topic="Welcome to our server, please register.",
                    default_messages=[
                        """
                        **Welcome to our Discord server! Please register using the <#registration-form>**

                        If you encounter any problems with registration, please ask in <#registration-help>.
                        """,
                    ],
                    permission_overwrites=[
                        PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["send_messages"]),
                        PermissionOverwrite(roles=ROLES_REGISTERED, deny=["view_channel"]),
                        PermissionOverwrite(roles=ROLES_ORGANIZERS, allow=["view_channel"]),
                    ],
                ),
                TextChannel(
                    name="registration-form",
                    topic="Please follow the registration instructions.",
                    permission_overwrites=[
                        PermissionOverwrite(roles=[ROLE_EVERYONE], deny=["send_messages"]),
                        PermissionOverwrite(roles=ROLES_REGISTERED, deny=["view_channel"]),
                        PermissionOverwrite(roles=ROLES_ORGANIZERS, allow=["view_channel"]),
                    ],
                ),
                ForumChannel(
                    name="registration-help",
                    topic="""
                        # This channel is only for asking for help with registration, not for general discussion.

                        As this community is only intended for EuroPython participants, there are no public discussion channels.
                        """,
                    permission_overwrites=[
                        PermissionOverwrite(roles=ROLES_REGISTERED, deny=["view_channel"]),
                        PermissionOverwrite(roles=ROLES_ORGANIZERS, allow=["view_channel"]),
                    ],
                ),
                TextChannel(
                    name="registration-log",
                    topic="The EuroPython bot will log registration actions here to help us with debugging.",
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=[ROLE_EVERYONE],
                            deny=["view_channel"],
                        )
                    ],
                ),
                TextChannel(
                    name="system-events",
                    topic='This channel will show "raw" joins to keep track of who joins and who registered without diving into the audit log.',
                    permission_overwrites=[
                        PermissionOverwrite(
                            roles=[ROLE_EVERYONE],
                            deny=["view_channel"],
                        )
                    ],
                ),
            ],
        ),
    ],
)


def report_error(message: str) -> None:
    """Print an error message to stderr."""
    print("ERROR:", message, file=sys.stderr)


def create_permissions(permissions: list[Permission]) -> discord.Permissions:
    return discord.Permissions(
        **{perm: True for perm in permissions},
    )


async def ensure_channel_permissions(
    guild: discord.Guild,
    channel: discord.CategoryChannel | discord.TextChannel | discord.ForumChannel,
    permission_overwrite_templates: list[PermissionOverwrite],
) -> None:
    logger.info("Ensure permissions for channel %s", channel.name)

    logger.debug("Accumulating expected permission overwrites")
    expected_overwrites_by_role: dict[str, dict[str, bool]] = defaultdict(dict)
    for overwrite_template in permission_overwrite_templates:
        for role_name in overwrite_template.roles:
            for permission in overwrite_template.allow:
                expected_overwrites_by_role[role_name][permission] = True
            for permission in overwrite_template.deny:
                expected_overwrites_by_role[role_name][permission] = False

    logger.debug("Determine if update is required")
    # Enabling some settings for some roles sometimes enables it also for @everyone.
    # Workaround: If any update is required, do a full update
    update_required = False
    updates_by_role: dict[discord.Role, discord.PermissionOverwrite] = {}
    for role_name, expected_overwrites in expected_overwrites_by_role.items():
        role = discord_get(guild.roles, name=role_name)
        current_permissions = channel.permissions_for(role)
        for permission, expected_value in expected_overwrites.items():
            current_value = getattr(current_permissions, permission)
            if current_value != expected_value:
                update_required = True
        updates_by_role[role] = discord.PermissionOverwrite(**expected_overwrites)

    if update_required:
        logger.debug("Update permissions")
        await channel.edit(overwrites=updates_by_role)


async def ensure_category_and_channel_permissions(
    guild: discord.Guild, category_templates: list[Category]
) -> None:
    for category_template in category_templates:
        for channel_template in category_template.channels:
            channel = discord.utils.get(guild.channels, name=channel_template.name)
            await ensure_channel_permissions(
                guild,
                channel,
                category_template.permission_overwrites + channel_template.permission_overwrites,
            )


async def ensure_category(
    guild: discord.Guild, *, name: str, position: int
) -> discord.CategoryChannel:
    """Ensure the category exists at the expected position."""
    logger.info("Ensure category %s at position %d", name, position)
    category = discord_get(guild.categories, name=name)
    if category is None:
        logger.debug("Create category")
        return await guild.create_category(name, position=position)

    logger.debug("Found category")
    if category.position != position:
        logger.debug("Update position")
        await category.edit(position=position)
    return category


async def ensure_text_channel(
    guild: discord.Guild,
    name: str,
    *,
    category: discord.CategoryChannel | None,
    position: int,
) -> discord.TextChannel:
    """Ensure the text channel exists at the expected position."""
    logger.info("Ensure text channel %s at position %d", name, position)
    channel = discord_get(guild.text_channels, name=name)
    if channel is None:
        logger.debug("Create text channel %s", name)
        return await guild.create_text_channel(name=name, category=category, position=position)

    logger.debug("Found text channel")
    if channel.category != category:
        logger.debug("Update category")
        await channel.edit(category=category)
    if channel.position != position:
        logger.debug("Update position")
        await channel.edit(position=position)
    return channel


async def ensure_tags(
    channel: discord.ForumChannel, expected_tags: list[str], *, require_tag: bool
) -> None:
    """Ensure the expected tag configuration for a forum channel."""
    logger.info("Ensure tags %s for channel %s", expected_tags, channel.name)
    existing_tags = {tag.name: tag for tag in channel.available_tags}
    tags_to_create = set(expected_tags) - set(existing_tags)

    if tags_to_create:
        for tag_name in tags_to_create:
            logger.debug("Create tag %s", tag_name)
            existing_tags[tag_name] = await channel.create_tag(name=tag_name)

        logger.debug("Update available tags for channel %s", channel.name)
        await channel.edit(available_tags=(list(existing_tags.values())))

    if require_tag and not channel.flags.require_tag:
        logger.debug("Update 'require_tag' flag")
        await channel.edit(require_tag=require_tag)


async def ensure_forum_channel(
    guild: discord.Guild,
    name: str,
    *,
    category: discord.CategoryChannel,
    position: int,
    expected_tags: list[str] | None,
    require_tag: bool,
) -> None:
    """Ensure the text channel exists at the expected position with the expected tags."""
    logger.info("Configure forum channel %s at position %d", name, position)
    channel = discord_get(guild.forums, name=name)
    if channel is None:
        logger.debug("Create forum channel %s", name)
        channel = await guild.create_forum(name, category=category, position=position)
    else:
        logger.debug("Found forum channel")
        if channel.category is None or channel.category != category:
            logger.debug("Update category")
            await channel.edit(category=category)
        if channel.position != position:
            logger.debug("Update position")
            await channel.edit(position=position)

    await ensure_tags(channel, expected_tags, require_tag=require_tag)


async def ensure_role(guild: discord.Guild, template: Role) -> None:
    """Ensure the role exists with the expected configuration."""
    logger.info("Ensure role %s", template.name)
    permissions = create_permissions(template.permissions)
    expected_color = discord.Color.from_str(template.color)

    role = discord_get(guild.roles, name=template.name)
    if role is None:
        logger.debug("Create role %s", template.name)
        await guild.create_role(
            name=template.name,
            colour=expected_color,
            hoist=template.hoist,
            mentionable=template.mentionable,
            permissions=permissions,
        )
    else:
        logger.debug("Found role")
        if role.name != "@everyone" and role.colour != expected_color:
            logger.debug("Update color")
            await role.edit(colour=expected_color)
        if role.hoist != template.hoist:
            logger.debug("Update hoist")
            await role.edit(hoist=template.hoist)
        if role.mentionable != template.mentionable:
            logger.debug("Update mentionable")
            await role.edit(mentionable=template.mentionable)
        permissions = permissions
        if role.permissions != permissions:
            logger.debug("Update permissions")
            await role.edit(permissions=permissions)


async def configure_guild(guild: discord.Guild, template: GuildConfig) -> None:
    logger.info("Configuring roles")
    for role_template in template.roles:
        await ensure_role(guild, role_template)

    logger.info("Configuring 'COMMUNITY' features")
    await ensure_community_feature(
        guild,
        rules_channel_name=template.rules_channel_name,
        updates_channel_name=template.updates_channel_name,
    )

    logger.info("Configuring categories and channels")
    await ensure_categories_and_channels(guild, template.categories)

    logger.info("Configuring system channels and events")
    await ensure_system_channel_configuration(
        guild,
        system_channel_name=template.system_channel_name,
        updates_channel_name=template.updates_channel_name,
        rules_channel_name=template.rules_channel_name,
    )

    logger.info("Configuring permissions")
    await ensure_category_and_channel_permissions(guild, template.categories)

    logger.info("Configure channel topics")
    await ensure_channel_topics(guild, template.categories)

    logger.info("Configure channel default messages")
    await ensure_default_messages(guild, template.categories)


async def ensure_default_messages(guild: discord.Guild, categories: list[Category]) -> None:
    logger.info("Ensure default messages")
    for category_template in categories:
        for channel_template in category_template.channels:
            if not isinstance(channel_template, TextChannel):
                continue
            if not channel_template.default_messages:
                continue
            channel = discord_get(guild.channels, name=channel_template.name)
            await ensure_channel_messages(channel, channel_template.default_messages)


async def ensure_channel_messages(channel: discord.TextChannel, messages: list[str]) -> None:
    logger.info("Ensure channel messages for channel %s")
    existing_messages = []
    async for server_message in channel.history(limit=None, oldest_first=True):
        if not server_message.author.bot:
            logger.warning("Channel has messages from non-bot users, skipping message creation")
            return
        existing_messages.append(server_message)

    if [msg.content for msg in existing_messages] == messages:
        logger.debug("No update required")
        return

    for server_message in existing_messages:
        logger.debug("Deleting existing message")
        await server_message.delete()
    for new_message in messages:
        logger.debug("Send new message")
        await channel.send(content=new_message, suppress_embeds=True)


async def ensure_channel_topics(guild: discord.Guild, category_templates: list[Category]) -> None:
    logger.info("Ensure channel topics")
    for category_template in category_templates:
        for channel_template in category_template.channels:
            channel = discord_get(guild.channels, name=channel_template.name)
            expected_topic = channel_template.topic
            if channel.topic != expected_topic:
                logger.debug("Update topic of channel %s", channel_template.name)
                await channel.edit(topic=expected_topic)


async def ensure_system_channel_configuration(
    guild: discord.Guild,
    *,
    system_channel_name: str,
    updates_channel_name: str,
    rules_channel_name: str,
):
    logger.info("Ensure system channel configuration")
    current_system_channel = guild.system_channel
    if current_system_channel is None or current_system_channel.name != system_channel_name:
        logger.debug("Update system channel")
        new_system_channel = discord_get(guild.text_channels, name=system_channel_name)
        await guild.edit(system_channel=new_system_channel)

    current_updates_channel = guild.public_updates_channel
    if current_updates_channel is None or current_updates_channel.name != updates_channel_name:
        logger.debug("Update public updates channel")
        new_updates_channel = discord_get(guild.text_channels, name=updates_channel_name)
        await guild.edit(public_updates_channel=new_updates_channel)

    rules_channel = guild.rules_channel
    if rules_channel is None or rules_channel.name != rules_channel_name:
        logger.debug("Update rules channel")
        new_rules_channel = discord_get(guild.text_channels, name=rules_channel_name)
        await guild.edit(rules_channel=new_rules_channel)

    logger.debug("Ensure system channel flags")
    if not guild.system_channel_flags.join_notifications:
        logger.debug("Enable member join notifications to the system channel")
        await guild.edit(system_channel_flags=discord.SystemChannelFlags(join_notifications=True))
    if guild.system_channel_flags.join_notification_replies:
        logger.debug("Disable 'Wave to say Hi!' suggestion on member join events")
        await guild.edit(
            system_channel_flags=discord.SystemChannelFlags(join_notification_replies=False)
        )
    if guild.system_channel_flags.guild_reminder_notifications:
        logger.debug("Disable server setup suggestions and reminders")
        await guild.edit(
            system_channel_flags=discord.SystemChannelFlags(guild_reminder_notifications=False)
        )


async def ensure_categories_and_channels(
    guild: discord.Guild, category_templates: list[Category]
) -> None:
    # channel positions are global, not per-category
    channel_position = 0
    for category_position, category_template in enumerate(category_templates):
        category = await ensure_category(
            guild, name=category_template.name, position=category_position
        )

        for channel_template in category_template.channels:
            if isinstance(channel_template, TextChannel):
                await ensure_text_channel(
                    guild, channel_template.name, category=category, position=channel_position
                )
            elif isinstance(channel_template, ForumChannel):
                await ensure_forum_channel(
                    guild,
                    channel_template.name,
                    category=category,
                    position=channel_position,
                    expected_tags=channel_template.tags,
                    require_tag=channel_template.require_tag,
                )
            else:
                # hint for the type checker: report error if there can be more channel types
                assert_never(channel_template)

            channel_position += 1


async def ensure_community_feature(
    guild: discord.Guild, *, rules_channel_name: str, updates_channel_name: str
) -> None:
    logger.info("Ensure 'COMMUNITY' feature configuration")

    logger.debug("Ensure rules and public updates channels")
    rules_channel = discord_get(guild.text_channels, name=rules_channel_name)
    if rules_channel is None:
        rules_channel = await ensure_text_channel(
            guild, category=None, name=rules_channel_name, position=0
        )
    public_updates_channel = discord_get(guild.text_channels, name=updates_channel_name)
    if public_updates_channel is None:
        public_updates_channel = await ensure_text_channel(
            guild, category=None, name=updates_channel_name, position=0
        )

    if guild.verification_level < discord.VerificationLevel.medium:
        logger.debug("Raise verification level at medium")
        await guild.edit(verification_level=discord.VerificationLevel.medium)

    if "COMMUNITY" not in guild.features:
        logger.debug("Enable guild 'COMMUNITY' feature")
        await guild.edit(
            community=True,
            rules_channel=rules_channel,
            public_updates_channel=public_updates_channel,
            explicit_content_filter=discord.ContentFilter.all_members,
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
