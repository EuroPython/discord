from unittest import mock

import aiohttp
import pytest
import yarl
from aiohttp import client_reqrep
from tests.programme_notifications import factories

from extensions.programme_notifications import exceptions
from extensions.programme_notifications.domain import discord
from extensions.programme_notifications.services import api

_WEBHOOK_MESSAGE = discord.WebhookMessage(
    content="Message content",
    embeds=[
        discord.Embed(
            title="Embed title",
            author=discord.Author(name="Embed Author", icon_url="https://icon.url/icon.jpg"),
            description="Embed description",
            fields=[
                discord.Field(
                    name="field name",
                    value="field value",
                    inline=False,
                )
            ],
            footer=discord.Footer(text="Embed Footer"),
            url="https://link.url/embed",
        )
    ],
)
_EXPECTED_PAYLOAD = {
    "content": "Message content",
    "embeds": [
        {
            "title": "Embed title",
            "author": {"name": "Embed Author", "icon_url": "https://icon.url/icon.jpg"},
            "description": "Embed description",
            "fields": [{"name": "field name", "value": "field value", "inline": False}],
            "footer": {"text": "Embed Footer"},
            "url": "https://link.url/embed",
            "color": None,
        }
    ],
    "allowed_mentions": {"parse": []},
}


async def test_posts_message_to_discord_webhook(
    configuration_factory: factories.ConfigurationFactory,
    client_session: mock.Mock,
) -> None:
    """Delivers message to a single webhook select by identifier."""
    # GIVEN a webhook message
    webhook_message = _WEBHOOK_MESSAGE
    # AND a configuration instance
    config = configuration_factory({"webhooks": {"webhook": "https://discord.org/1234"}})
    # AND a mocked client session with an async post method
    client_session.post = mock.AsyncMock()
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN that message is posted to a webhook
    await client.execute_webhook(webhook_message, webhook="webhook")

    # THEN the post method was called with the appropriate arguments
    client_session.post.assert_awaited_once_with(
        url=yarl.URL("https://discord.org/1234"), json=_EXPECTED_PAYLOAD, raise_for_status=True
    )


async def test_failing_webhook_does_not_reveal_webhook_url(
    configuration_factory: factories.ConfigurationFactory,
    client_session: mock.Mock,
) -> None:
    """Exceptions should not contain URLs, as URLs contain tokens."""
    # GIVEN a webhook message
    webhook_message = _WEBHOOK_MESSAGE
    # AND a configuration instance
    config = configuration_factory({"webhooks": {"webhook": "https://discord.org/1234"}})
    # AND a mocked client session a failing post method
    client_session.post = mock.AsyncMock(
        side_effect=aiohttp.ClientResponseError(
            request_info=mock.create_autospec(client_reqrep.RequestInfo),
            history=(),
            headers={},
            status=403,
            message="Permission denied!",
        )
    )
    # AND an api client with that session and configuration repository
    client = api.ApiClient(session=client_session, config=config)

    # WHEN that message is posted to a webhook
    # THEN a WebhookDeliveryError is raised
    with pytest.raises(exceptions.WebhookDeliveryError) as exc_info:
        await client.execute_webhook(webhook_message, webhook="webhook")

    # AND the exception has no "__cause__"
    assert exc_info.value.__cause__ is None
    # AND the exception context is suppressed
    assert exc_info.value.__suppress_context__
    # AND the raised exception contains the name of the failing webhook
    assert exc_info.value.webhook == "webhook"
    # AND the raised exception contains the response status
    assert exc_info.value.status == 403
    # AND the raised exception contains the response message
    assert exc_info.value.message == "Permission denied!"
