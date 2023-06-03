# discord
This is discord playground \o/


# Setting up the bot and the server
👉 Any developer should activate "Developer Mode" in Discord.
You find it in the User Settings / App Settings / Advanced

You can setup a bot in https://discord.com/developers/applications/
Here you need to keep a note of the Application ID (also referred to as client_id)
and the bot token in the "Bot" section. If a bot token is leaked out, you can reset it here.

In the "OAuth2" use the "OAuth2 URL Generator" to create the permissions for the bot
Once you have a bot, you can invite the bot to your server through an URL like this:
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=YOUR_PERMISSIONS&scope=bot.
You need to be logged in into Discord for this to work.

*TBD: The exact minimum permissions we expect.*


# How to setup and start-
We are targeting Python 3.10 with pipenv. For other tools, look at the pipfile and
create a virtual environment and install the libraries manually.

Create a configuation.yaml copy (or change it) to reflect your own bot,
discord server, role and channel names

You can hide configuration secrets in the file by setting them to "*".
If you do that, the code will look in your ".env" file and/or may later
search your environment as well. Secrets currently are DISCORD_BOT_TOKEN and
DISCORD_SERVER_ID.

Then start the bot with 

    python src/main.py *configuation.yaml*

where *configuation.yaml* is the name of the file.


# Pretix integration
The file `pretix_connector.py` is the entry point to interaction with pretix.
The communication is read-only from pretix.

Currently, it has one function "get_ticket_roles_from_message_with_ticket_id" 
which receives a text message and tries to guess if anything is a valid ticket_id.

If something matches, return a list of roles.

Since roles are shared between bot, pretix and later database, all roles need a definition in
the `model.py` file.


# Data persistence and logging.
To be defined.