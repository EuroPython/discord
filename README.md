# PyConESBot Discord Bot

An easy to deploy conference bot that manages roles for attendees via registration, notifies about upcoming sessions.
Exposes Discord server statistics to organizers.
We hosted the bot on Hetzner. And deployed with a single click Action from GitHub 😎.

![registration_view.png](./img/registration_view.png)

## Overview

The `main` method in `PyConESBot/bot.py` is the entry point for the bot.
I't a good starting point to start browsing the codebase.
It requires a `.secrets` file in the root of the repository with `DISCORD_BOT_TOKEN` and `PRETIX_TOKEN` environment variables.

### Registration

At PyConES, we use [pretix](https://pretix.eu/about/en/) as our ticketing system.

The bot utilizes the Pretix API to fetch ticket information and creates an in-memory key-value store to retrieve the ticket type for a given Discord user. The mapping between ticket types and Discord roles is defined in a JSON file, such as ticket_to_roles_prod.json, and is used by the bot to assign roles to users.

There are safeguard methods in place to prevent users from registering multiple times and to make a direct Pretix API call in case the user information is not available in the in-memory store.


### Program notifications

Is a service to push the programme notification to Discord. Pretalx API is used to fetch the programme information, and `config.toml` holds information about livestream URLs.

### Organizers extension
A set of commands that are available only for organizers that are allowing to get statistics about the Discord server.

## Setup
### Install Rye (Linux systems)
```shell
# dependencies of readline, sqlite3, ctypes
sudo apt install libreadline-dev libsqlite3-dev lzma libbz2-dev liblzma-dev

# rye
curl -sSf https://rye.astral.sh/get | bash

# add the required info to the .profile file if your system supports it. Otherwise, consider
# using .bashrc, .zshrc, etc. More info at: https://rye.astral.sh/guide/installation/#add-shims-to-path
echo 'source "$HOME/.rye/env"' >> ~/.profile
```

### Using Rye
This is a summary of useful `rye` commands.
Please refer to the [Rye documentation](https://rye.astral.sh/guide/basics/) for details.

```shell
# generate venv from pyproject.toml
rye sync

# install package and update all other packages
rye add package
rye add --dev package  # install as dev dependency

# remove package
rye remove package
```

### Clone repo, install dependencies, run tests
```shell
# clone repo, install dependencies
git clone https://github.com/Javinator9889/pycones-discord-bot.git
cd pycones-discord-bot

# install dependencies
rye sync

# run linting and tests
rye run black --check .
rye run isort --check .
rye run flake8 .
rye run pytest .
```

### Configuration
Create `config.local.toml` file in PyConESBot directory, it would be used instead of `config.toml` if exists.

Add `.secrets` file to the root of the repository with the following content:
```shell
DISCORD_BOT_TOKEN=<PyConESBotToken>
PRETIX_TOKEN=<PretixStagingToken>
````
After you have added the `.secrets` file, you can run the bot with the following command:
```shell
rye run python PyConESBot/bot.py
```
or with docker:
```shell
docker build --tag pycones-discord_bot .
docker run --interactive --tty --env DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN --env PRETIX_TOKEN=$PRETIX_TOKEN pycones-discord_bot
```
