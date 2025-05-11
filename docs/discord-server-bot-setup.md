# Discord Server and Bot Setup

Follow this guide to

* Create a Discord Server
* Create a Discord Bot
* Connect the Bot to the Server

NOTE: These steps require a Discord account with two-factor authentication enabled.

## Create the Server

In the left sidebar of the Discord Window, click the button "Add a Server":

![Discord: Add a Server](img/add-server.png)

Select "Create My Own":

![Discord: Create My Own](img/create-my-own.png)

Skip further questions:

![Discord: Skip question](img/skip-question.png)

Configure the server name and icon (can be updated later), then click "Create":

![Discord: Server name and icon](img/server-name-and-icon.png)

Congratulations, you now have your own Discord server.

## Create a Bot

Go to https://discord.com/developers/applications/ and log in.

In the top-right corner, click "New Application".

![Bot: New Application](img/new-application.png)

Configure the application name (can be updated later), agree to the terms of service, and click "Create".

![Bot: Create Application](img/create-application.png)

In the left sidebar, go to "General Information" and configure the bot's icon and description (optional, can be updated later).

![Bot: Icon and Description](img/bot-icon-and-description.png)

Scroll down and configure the Terms of Service and Privacy Policy (optional, can be updated later).

![Bot: ToS and Privacy Policy](img/bot-tos-privacy.png)

In the left sidebar, go to "Installation".
Remove the option "User install" and set the Install Link to "None".

![Bot: Install configuration](img/bot-install-config.png)

In the left sidebar, go to "Bot", then scroll down to "Privileged Gateway Intents".
Activate "Server Member Intent" and "Message Content Intent".
Click "Save Changes".

![Bot: Configure Intents](img/configure-intents.png)

In the left sidebar, go to "OAuth2".
Select the scope "bot" and the permission "Administrator".

![Bot: Scope and Permissions](img/bot-scopes-and-permissions.png)

Scroll down, configure the integration type "Guild Install", and copy the URL.

![Bot: Integration URL](img/bot-integration-url.png)

Open the copied URL in a web browser. You will be prompted to open the Discord app.

![Bot: Open in Discord](img/bot-open-in-discord.png)

Proceed to add the bot to your server.

![Bot: Add to Server](img/bot-add-to-server.png)

Confirm the assigned permissions.

![Bot: Confirm Permissions](img/bot-confirm-permissions.png)

Congratulations, you created a bot and added it to a server.

![Bot: Post-Installation Screen](img/bot-post-install-screen.png)

## Use the Bot

To use the bot from Python, you need an authorization token.

Go back to https://discord.com/developers/applications/.
In the left sidebar, go to "Bot", and click "Reset Token".

![Bot: Reset Token](img/bot-reset-token.png)

Confirm that step. This might require a two-factor authentication confirmation.

![Bot: Confirm Token Reset](img/bot-confirm-token-reset.png)

Copy your new token and store it somewhere safe.

![Bot: Copy Token](img/bot-copy-token.png)

To confirm the installation, install the Python package [discord.py](https://pypi.org/project/discord.py/)
(e.g. with `pip install discord.py`), and run the following script (add your bot token at `BOT_TOKEN = "..."`):

```python
import asyncio

import discord
from discord.ext import commands

BOT_TOKEN = "..."


class Bot(commands.Bot):
    async def on_ready(self):
        print("ready", self.user.name, self.user.id)


class Ping(commands.Cog):
    @commands.hybrid_command(name="ping")
    async def ping(self, context):
        await context.send("Pong!")


async def main():
    prefix = commands.when_mentioned_or("$")

    intents = discord.Intents(messages=True, message_content=True)
    async with Bot(command_prefix=prefix, intents=intents) as bot:
        await bot.add_cog(Ping())
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
```

In Discord, go to your server and write the message `$ping` in a text channel.
The bot should respond with `Pong!`.

![Bot: Ping Pong](img/bot-ping-pong.png)

You can now stop the Python script by pressing Ctrl+C.
