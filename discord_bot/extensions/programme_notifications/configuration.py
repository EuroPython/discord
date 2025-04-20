import os
from collections.abc import Mapping
from typing import Final

import arrow
import attrs
import cattrs
import toml
import yarl
from attrs import validators

from discord_bot import configuration

_WEBHOOK_ENVVAR_PREFIX: Final = "DISCORD_WEBHOOK_"

# Simplified validators
_INSTANCE_OF_STR = validators.instance_of(str)
_INSTANCE_OF_URL = validators.instance_of(yarl.URL)
_INSTANCE_OF_DT = validators.instance_of(arrow.Arrow)
_INSTANCE_OF_BOOL = validators.instance_of(bool)
_PRETALX_TALK_URL = validators.and_(_INSTANCE_OF_STR, lambda _i, _a, u: "{code}" in u)
# _API_SESSION_URL = validators.and_(_INSTANCE_OF_STR, lambda _i, _a, u: "{code}" in u)
# _WEBSITE_SESSION_URL = validators.and_(_INSTANCE_OF_STR, lambda _i, _a, u: "{slug}" in u)
_URL_MAPPING = validators.deep_mapping(_INSTANCE_OF_STR, _INSTANCE_OF_URL)
_URL_LIST = validators.deep_iterable(_INSTANCE_OF_URL, validators.instance_of(list))


@attrs.define(frozen=True)
class RoomConfiguration:
    """Configuration for a room."""

    discord_channel_id: str = attrs.field(validator=validators.matches_re(r"\d+"))
    webhook_id: str
    livestreams: Mapping[str, str]


@attrs.define(frozen=True)
class NotificationChannel:
    """A webhook for schedule notifications with a session overview."""

    webhook_id: str
    include_channel_in_embeds: bool


@attrs.define(frozen=True)
class NotifierConfiguration:
    """Configuration for the schedule notifier."""

    timezone: str = attrs.field(validator=_INSTANCE_OF_STR)
    conference_days_first: arrow.Arrow = attrs.field(validator=_INSTANCE_OF_DT)
    conference_days_last: arrow.Arrow = attrs.field(validator=_INSTANCE_OF_DT)
    pretalx_talk_url: str = attrs.field(validator=_PRETALX_TALK_URL)
    # conference_website_session_base_url: str = attrs.field(validator=_WEBSITE_SESSION_URL)
    # conference_website_api_session_url: str = attrs.field(validator=_API_SESSION_URL)
    pretalx_schedule_url: str = attrs.field(validator=_INSTANCE_OF_STR)
    slido_url: str = attrs.field(validator=_INSTANCE_OF_STR)
    notification_channels: list[NotificationChannel]
    rooms: Mapping[str, RoomConfiguration]
    webhooks: Mapping[str, yarl.URL] = attrs.field(repr=False, validator=_URL_MAPPING)
    timewarp: bool = attrs.field(validator=_INSTANCE_OF_BOOL, default=False)

    @classmethod
    def from_environment(cls, config: configuration.Config) -> "NotifierConfiguration":
        """Create a NotifierConfiguration from the environment."""
        with config.CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            notifier_config = toml.load(config_file)["programme_notifications"]

        notifier_config["webhooks"] = {
            key.removeprefix(_WEBHOOK_ENVVAR_PREFIX): value
            for key, value in os.environ.items()
            if key.startswith(_WEBHOOK_ENVVAR_PREFIX)
        }
        timezone = notifier_config["timezone"]
        converter = cattrs.Converter()
        converter.register_structure_hook(arrow.Arrow, lambda v, _: arrow.get(v, tzinfo=timezone))
        converter.register_structure_hook(yarl.URL, lambda v, t: t(v))
        return converter.structure(notifier_config, cls)
