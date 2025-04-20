"""Tests for creating an embed to show session information.

Information for the embed is fetched from various sources, like Pretalx,
a EuroPython API, and the configuration file. The information needs to
be combined to create Discord embed.

As we're sending embeds to webhooks in other Discord communities, the
Discord channel information is optional: Members of other communities
do not have access to the room channel in the EuroPython 2023 server.
"""

import arrow
import pytest
import yarl

from discord_bot.extensions.programme_notifications.domain import discord, europython, services
from tests.programme_notifications import factories


def test_create_embed_from_session_information() -> None:
    """Create an embed if all session information is available."""
    # GIVEN a EuroPython session instance
    europython_session = europython.Session(
        code="ABCDEF",
        title="A Tale of Two Pythons: Subinterpreters in Action!",
        abstract=(
            "Sometimes, having one, undivided interpreter just isn't enough. The pesky GIL,"
            " problems with isolation, and the difficult problem of concurrency haunt the dreams of"
            " even the most talented Python developer. Clearly, a good solution is needed and that"
            " solution is finally here: subinterpreters."
        ),
        track=europython.TranslatedString(en="Core Python"),
        duration=45,
        slot=europython.Slot(
            room_id=1234,
            room=europython.TranslatedString("The Broom Closet"),
            start=arrow.Arrow(2023, 7, 19, 9, 55, 0, tzinfo="Europe/Prague"),
        ),
        speakers=[europython.Speaker(code="123456", name="Ada Lovelace", avatar="https://ada.avatar")],
        url=yarl.URL("https://ep.session/a-tale-of-two-pythons-subinterpreters-in-action"),
        livestream_url=yarl.URL("https://livestreams.com/best-conference-sessions-of-2023"),
        discord_channel_id="123456789123456",
    )
    slido_url = "https://app.sli.do/event/test"

    # WHEN an embed is created with that information
    embed = services.create_session_embed(europython_session, slido_url, include_discord_channel=True)

    # THEN the embed is equal to the expected embed
    session_url = "https://ep.session/a-tale-of-two-pythons-subinterpreters-in-action"
    assert embed == discord.Embed(
        title="A Tale of Two Pythons: Subinterpreters in Action!",
        author=discord.Author(name="Ada Lovelace", icon_url="https://ada.avatar"),
        description=(
            "Sometimes, having one, undivided interpreter just isn't enough. The pesky GIL,"
            " problems with isolation, and the difficult problem of concurrency haunt the dreams of"
            " even the most talented Python [...]"
            f"\n\n[Read more about this session]({session_url})"
        ),
        fields=[
            discord.Field(name="Start Time", value="<t:1689753300:f>", inline=True),
            discord.Field(name="Room", value="The Broom Closet", inline=True),
            discord.Field(name="Track", value="Core Python", inline=True),
            discord.Field(name="Duration", value="45 minutes", inline=True),
            discord.Field(
                name="Livestream",
                value="[Vimeo](https://livestreams.com/best-conference-sessions-of-2023)",
                inline=True,
            ),
            discord.Field(
                name="Live Q&A",
                value="[Slido](https://app.sli.do/event/test)",
                inline=True,
            ),
            discord.Field(name="Discord Channel", value="<#123456789123456>", inline=True),
        ],
        footer=discord.Footer(text="This session starts at 09:55:00 (local conference time)"),
        url=session_url,
    )


@pytest.mark.parametrize(
    ("session_title", "expected_embed_title"),
    [
        pytest.param(None, None, id="No title"),
        pytest.param("", None, id="Empty title"),
        pytest.param(
            "The Seven Wonders of Python: Builtins to the rescue!",
            "The Seven Wonders of Python: Builtins to the rescue!",
            id="Title that doesn't need to be shortened",
        ),
        pytest.param(
            (
                "A very verbose title that will not fit well in a Discord embed needs to be"
                " shortened to the point it doesn't disrupt the embed visually."
            ),
            (
                "A very verbose title that will not fit well in a Discord embed needs to be"
                " shortened to the point it doesn't disrupt the [...]"
            ),
            id="Title that doesn't need to be shortened",
        ),
    ],
)
def test_title_gets_formatted_according_to_maximum_width(
    session_title: str | None,
    expected_embed_title: str | None,
    session_factory: factories.SessionFactory,
) -> None:
    """Title fields don't support an 'infinite' length."""
    # GIVEN a session with a known session title
    session = session_factory(title=session_title)
    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed title is as expected
    assert embed.title == expected_embed_title


@pytest.mark.parametrize(
    ("abstract", "session_url", "expected_description"),
    [
        pytest.param(
            "",
            None,
            "*This session does not have an abstract.*",
            id="Empty abstract without session url",
        ),
        pytest.param(
            "",
            yarl.URL("https://foo.session"),
            ("*This session does not have an abstract.*\n\n[Read more about this session]" "(https://foo.session)"),
            id="Empty abstract but with session url",
        ),
        pytest.param(
            (
                "There's no need to shorten an abstract that has fewer characters than the defined"
                " maximum width. Thank you for coming to my abstract talk."
            ),
            None,
            (
                "There's no need to shorten an abstract that has fewer characters than the defined"
                " maximum width. Thank you for coming to my abstract talk."
            ),
            id="Abstract that does not need to be shortened without url",
        ),
        pytest.param(
            (
                "There's no need to shorten an abstract that has fewer characters than the defined"
                " maximum width. Thank you for coming to my abstract talk."
            ),
            yarl.URL("https://foo.session"),
            (
                "There's no need to shorten an abstract that has fewer characters than the defined"
                " maximum width. Thank you for coming to my abstract talk."
                "\n\n[Read more about this session](https://foo.session)"
            ),
            id="Abstract that does not need to be shortened but with a url",
        ),
        pytest.param(
            (
                "It's better to truncate very verbose abstracts to prevent the embeds from taking"
                " up too much space on screen. That's why abstracts have a maximum defined width"
                " and the function truncates abstracts that are too long.\n\nDo note that the"
                " truncation only happens on the abstract-part of the description. The URL behind"
                " the abstract is kept as-is to prevent it from becoming unusable or completely"
                " removed. That wouldn't be nice for our participants."
            ),
            None,
            (
                "It's better to truncate very verbose abstracts to prevent the embeds from taking"
                " up too much space on screen. That's why abstracts have a maximum defined width"
                " and the function truncates [...]"
            ),
            id="Abstract that needs to be shortened without url",
        ),
        pytest.param(
            (
                "It's better to truncate very verbose abstracts to prevent the embeds from taking"
                " up too much space on screen.\nThat's why abstracts have a maximum defined width"
                " and the function truncates abstracts that are too long.\n\nDo note that the"
                " truncation only happens on the abstract-part of the description. The URL behind"
                " the abstract is kept as-is to prevent it from becoming unusable or completely"
                " removed. That wouldn't be nice for our participants."
            ),
            yarl.URL("https://foo.session"),
            (
                "It's better to truncate very verbose abstracts to prevent the embeds from taking"
                " up too much space on screen. That's why abstracts have a maximum defined width"
                " and the function truncates [...]"
                "\n\n[Read more about this session](https://foo.session)"
            ),
            id="Abstract that needs to be shortened but with a url",
        ),
    ],
)
def test_abstract_gets_formatted_including_width_and_session_url(
    abstract: str,
    session_url: yarl.URL,
    expected_description: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Abstracts may be shortened and a url is added if available."""
    # GIVEN a session with a known abstract and session url
    session = session_factory(abstract=abstract, url=session_url)
    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed description is as expected
    assert embed.description == expected_description


@pytest.mark.parametrize(
    ("speakers", "expected_author"),
    [
        pytest.param([], None, id="No speakers"),
        pytest.param(
            [
                {"code": "123456", "name": "Ada Lovelace", "avatar": "https://ada.avatar"},
            ],
            discord.Author(name="Ada Lovelace", icon_url="https://ada.avatar"),
            id="One speakers",
        ),
        pytest.param(
            [
                {"code": "123456", "name": "Ada Lovelace", "avatar": "https://ada.avatar"},
                {"code": "654321", "name": "Alan Turing", "avatar": "https://turing.png"},
            ],
            discord.Author(name="Ada Lovelace & Alan Turing", icon_url="https://ada.avatar"),
            id="Two speakers",
        ),
        pytest.param(
            [
                {"code": "121314", "name": "Barbara Liskov", "avatar": "https://barbara.jpg"},
                {"code": "123456", "name": "Ada Lovelace", "avatar": "https://ada.avatar"},
                {"code": "654321", "name": "Alan Turing", "avatar": "https://turing.png"},
            ],
            discord.Author(name="Barbara Liskov, Ada Lovelace, & Alan Turing", icon_url="https://barbara.jpg"),
            id="More than two speakers",
        ),
        pytest.param(
            [
                {"code": "121314", "name": "Barbara Liskov", "avatar": None},
                {"code": "123456", "name": "Ada Lovelace", "avatar": "https://ada.avatar"},
                {"code": "654321", "name": "Alan Turing", "avatar": "https://turing.png"},
            ],
            discord.Author(name="Barbara Liskov, Ada Lovelace, & Alan Turing", icon_url="https://ada.avatar"),
            id="Fetch avatar url from non-first speaker",
        ),
        pytest.param(
            [
                {"code": "121314", "name": "Barbara Liskov", "avatar": None},
                {"code": "123456", "name": "Ada Lovelace", "avatar": None},
                {"code": "654321", "name": "Alan Turing", "avatar": None},
            ],
            discord.Author(name="Barbara Liskov, Ada Lovelace, & Alan Turing", icon_url=None),
            id="No speakers with avatars",
        ),
        pytest.param(
            [
                {"code": "121314", "name": "Barbara Liskov", "avatar": "https://barbara.jpg"},
                {"code": "123456", "name": "Ada Lovelace", "avatar": "https://ada.avatar"},
                {"code": "654321", "name": "Alan Turing", "avatar": "https://turing.png"},
                {
                    "code": "654321",
                    "name": (
                        "Very Long Name That Means That The Speaker Names Don't Fit The Maximum"
                        " Author Field Length And Should Be Truncated To Make Sure We Do Not"
                        " Violate Discord's Hard Limits On Author Length As That Would Mean"
                        " Getting A Bad Request Response From Discord"
                    ),
                    "avatar": "https://turing.png",
                },
            ],
            discord.Author(
                name=(
                    "Barbara Liskov, Ada Lovelace, Alan Turing, & Very Long Name That Means That"
                    " The Speaker Names Don't Fit The Maximum Author [...]"
                ),
                icon_url="https://barbara.jpg",
            ),
            id="Long author field gets truncated",
        ),
    ],
)
def test_include_speakers_in_embed_author_field(
    speakers: list[europython.Speaker],
    expected_author: discord.Author | None,
    session_factory: factories.SessionFactory,
) -> None:
    """Format speakers to a single author field."""
    # GIVEN a pretalx session instance
    pretalx_session = session_factory(speakers=speakers)
    # WHEN an embed is created with that information
    embed = services.create_session_embed(pretalx_session)

    # THEN the author is as expected
    assert embed.author == expected_author


@pytest.mark.parametrize(
    ("session_url", "expected_embed_url"),
    [
        pytest.param(
            yarl.URL("https://url.to.session/session"),
            "https://url.to.session/session",
            id="URL is available",
        ),
        pytest.param(None, None, id="URL is not available"),
    ],
)
def test_embed_gets_url_if_session_url_is_available(
    session_url: yarl.URL | None,
    expected_embed_url: str | None,
    session_factory: factories.SessionFactory,
) -> None:
    """If possible, make the embed link to the session page."""
    # GIVEN a session with a known session url
    session = session_factory(url=session_url)
    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed url is as expected
    assert embed.url == expected_embed_url


def test_start_time_is_available_in_embed(
    session_factory: factories.SessionFactory,
) -> None:
    """Show a localized Discord timestamp & conference local time."""
    # GIVEN a session with a known start time
    session = session_factory(
        slot={
            "room_id": 1234,
            "room": {"en": "The Broom Closet"},
            "start": "2023-07-19T09:55:00+02:00",
        }
    )
    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the start time in the embed is a Discord timestamp
    assert embed.fields[0].value == "<t:1689753300:f>"
    # AND the footer contains the local conference time
    assert embed.footer == discord.Footer("This session starts at 09:55:00 (local conference time)")


@pytest.mark.parametrize(
    ("slot", "expected_room_name"),
    [
        pytest.param(
            {
                "room_id": 1234,
                "room": {"en": "The Broom Closet"},
                "start": "2023-07-19T09:55:00+02:00",
            },
            "The Broom Closet",
            id="The room name is available",
        ),
        pytest.param(
            {"room_id": 1234, "room": dict(en=""), "start": "2023-07-19T09:55:00+02:00"},
            "—",
            id="The room name is empty",
        ),
        pytest.param(
            {"room_id": 1234, "room": None, "start": "2023-07-19T09:55:00+02:00"},
            "—",
            id="The room name is unavailable in the slot",
        ),
    ],
)
def test_room_is_displayed_correctly(
    slot: europython.Slot | None,
    expected_room_name: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Show the room name or a placeholder if unavailable."""
    # GIVEN a session with a known slot
    session = session_factory(slot=slot)

    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed url is as expected
    assert embed.fields[1].value == expected_room_name


@pytest.mark.parametrize(
    ("track", "expected_track_value"),
    [
        pytest.param({"en": "Core Python"}, "Core Python", id="The track is available"),
        pytest.param({"en": ""}, "—", id="The track name is empty"),
        pytest.param(None, "—", id="The track name is unavailable"),
    ],
)
def test_track_is_displayed_correctly(
    track: europython.TranslatedString | None,
    expected_track_value: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Show the track name or a placeholder if unavailable."""
    # GIVEN a session with a known track
    session = session_factory(track=track)

    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed url is as expected
    assert embed.fields[2].value == expected_track_value


@pytest.mark.parametrize(
    ("duration", "expected_duration_value"),
    [
        pytest.param(
            30,
            "30 minutes",
            id="30 minutes",
        ),
        pytest.param(
            45,
            "45 minutes",
            id="45 minutes",
        ),
        pytest.param(
            0,
            "—",
            id="Duration appears to be zero",
        ),
        pytest.param(
            None,
            "—",
            id="Duration is unknown",
        ),
    ],
)
def test_duration_is_displayed_correctly(
    duration: int | None,
    expected_duration_value: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Show the session duration, if available."""
    # GIVEN a session with a known duration
    session = session_factory(duration=duration)

    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed url is as expected
    assert embed.fields[3].value == expected_duration_value


@pytest.mark.parametrize(
    ("livestream_url", "expected_livestream_value"),
    [
        pytest.param(
            None,
            "—",
            id="No livestream URL available",
        ),
        pytest.param(
            yarl.URL("https://some.stream.live/"),
            "[Vimeo](https://some.stream.live/)",
            id="Livestream URL is available",
        ),
    ],
)
def test_livestream_url_is_displayed_if_available(
    livestream_url: yarl.URL | None,
    expected_livestream_value: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Show a livestream url, if available."""
    # GIVEN a session with a livestream url
    session = session_factory(livestream_url=livestream_url)

    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed url is as expected
    assert embed.fields[4].value == expected_livestream_value


@pytest.mark.parametrize(
    ("slido_url", "expected_slido_value"),
    [
        pytest.param(
            None,
            "—",
            id="No slido URL available",
        ),
        pytest.param(
            yarl.URL("https://app.sli.do/event/test"),
            "[Slido](https://app.sli.do/event/test)",
            id="Slido URL is available",
        ),
    ],
)
def test_slido_url_is_displayed_if_available(
    slido_url: yarl.URL | None,
    expected_slido_value: str,
    session_factory: factories.SessionFactory,
) -> None:
    """Show a slido url, if available."""
    # GIVEN a session
    session = session_factory()

    # WHEN the embed is created with slido_url
    embed = services.create_session_embed(session, slido_url=slido_url)

    # THEN the embed url is as expected
    assert embed.fields[5].value == expected_slido_value


def test_discord_channel_is_linked_if_available(
    session_factory: factories.SessionFactory,
) -> None:
    """Link to the Discord channel, if available and enabled."""
    # GIVEN a session with a discord channel
    session = session_factory(discord_channel_id="123456789123456")

    # WHEN the embed is created
    embed = services.create_session_embed(session, include_discord_channel=True)

    # THEN the embed shows the Discord channel
    assert embed.fields[6].value == "<#123456789123456>"


@pytest.mark.parametrize(
    ("discord_channel_id", "include_discord_channel"),
    [
        pytest.param("1234567890", False, id="Show experience if Discord channel is disabled"),
        pytest.param(None, True, id="Show experience if Discord channel is unavailable"),
        pytest.param(None, False, id="Experience if Discord channel is unavailable & disabled"),
    ],
)
def test_show_experience_if_discord_channel_is_unavailable(
    discord_channel_id: str | None,
    include_discord_channel: bool,
    session_factory: factories.SessionFactory,
) -> None:
    """Show the experience level if we don't show a Discord channel."""
    # GIVEN a session without a discord channel but with experience
    session = session_factory(discord_channel_id=discord_channel_id, experience="intermediate")

    # WHEN the embed is created
    embed = services.create_session_embed(session, include_discord_channel=include_discord_channel)

    # THEN the embed does not the discord channel
    assert not any(field.name == "Discord Channel" for field in embed.fields)
    # BUT it does show the experience level
    assert embed.fields[6].name == "Python Level"
    assert embed.fields[6].value == "Intermediate"


def test_show_website_url_if_discord_channel_and_experience_are_unavailable(
    session_factory: factories.SessionFactory,
) -> None:
    """Without Discord channel and experience, display website URL."""
    # GIVEN a session without a discord channel and experience level
    session = session_factory(discord_channel_id=None, experience=None)
    # WHEN the embed is created
    embed = services.create_session_embed(session, include_discord_channel=True)

    # THEN the embed does not the discord channel or experience
    assert not any(f.name == "Python Level" or f.name == "Discord Channel" for f in embed.fields)
    # BUT it does show a link to the europython website
    assert embed.fields[6].name == "PyCon/PyData Website"
    assert embed.fields[6].value == "[2025.pycon.de](https://2025.pycon.de)"


@pytest.mark.parametrize(
    ("experience", "expected_color"),
    [
        pytest.param(None, None, id="Experience is not available"),
        pytest.param("great", None, id="Experience is not recognized"),
        pytest.param("advanced", 13846600, id="Advanced experience matches schedule color"),
        pytest.param("intermediate", 16764229, id="Intermediate experience matches schedule color"),
        pytest.param("novice", 6542417, id="Beginner experience matches schedule color"),
    ],
)
def test_embed_color_reflects_audience_experience(
    experience: str | None, expected_color: int | None, session_factory: factories.SessionFactory
) -> None:
    """Color the embed using the level colors used on the website."""
    # GIVEN a session with a known audience experience level
    session = session_factory(experience=experience)

    # WHEN the embed is created
    embed = services.create_session_embed(session)

    # THEN the embed color is as expected
    assert embed.color == expected_color
