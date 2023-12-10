# Europython 2023 Discord Bot

An easy to deploy conference bot that manages roles for attendees via registration, notifies about upcoming sessions.
Exposes Discord server statistics to organizers.
We hosted the bot on Hetzner. And deployed with a single click Action from GitHub 😎.

![registration_view.png](./img/registration_view.png)

## Overview

The `main` method in `EuroPythonBot/bot.py` is the entry point for the bot.
I't a good starting point to start browsing the codebase.
It requires a `.secrets` file in the root of the repository with `DISCORD_BOT_TOKEN` and `PRETIX_TOKEN` environment variables.

### Registration

At EuroPython we use [pretix](https://pretix.eu/about/en/) as our ticketing system.

The bot uses the pretix API to fetch the ticket information and create in-memory key-value store to retrieve the ticket type for a given discord user.
The mapping between ticket types and discord roles is defined in JSON file, e.g. see `ticket_to_roles_prod.json` and is used by the bot to assign roles to users.

There are safeguard methods preventing users to register multiple times and to make a direct pretix API call in case the user information is not available in the in-memory store.


### Program notifications

Is a service to push the programme notification to Discord. Pretalx API is used to fetch the programme information, and `config.toml` holds information about livestream URLs.

### Organizers extension
A set of commands that are available only for organizers that are allowing to get statistics about the Discord server.

## Setup
Create `config.local.toml` file in EuroPythonBot directory, it would be used instead of `config.toml` if exists.

Add `.secrets` file to the root of the repository with the following content:
```shell
DISCORD_BOT_TOKEN=<EuroPythonTestBotToken_from_1Password>
PRETIX_TOKEN=<PretixStagingToken_from_1Password>
````
After you have added the `.secrets` file, you can run the bot with the following command:
```shell
pipenv run python EuroPythonBot/bot.py
```
or with docker:
```shell
docker build --tag discord_bot .
docker run --interactive --tty --env DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN --env PRETIX_TOKEN=$PRETIX_TOKEN discord_bot
```
