# Europython Discord Bot

An easy to deploy conference bot that manages roles for attendees via registration, notifies about upcoming sessions.
Exposes Discord server statistics to organizers.
We hosted the bot on Hetzner. And deployed with a single click Action from GitHub 😎.

![registration_view.png](./img/registration_view.png)

## Overview

The `main` method in `EuroPythonBot/bot.py` is the entry point for the bot.
I't a good starting point to start browsing the codebase.
It requires a `.secrets` file in the root of the repository with `DISCORD_BOT_TOKEN` and `PRETIX_TOKEN` environment variables.

### Registration

At EuroPython, we use [pretix](https://pretix.eu/about/en/) as our ticketing system.

The bot utilizes the Pretix API to fetch ticket information and creates an in-memory key-value store to retrieve the ticket type for a given Discord user. The mapping between ticket types and Discord roles is defined in a JSON file, such as ticket_to_roles_prod.json, and is used by the bot to assign roles to users.

There are safeguard methods in place to prevent users from registering multiple times and to make a direct Pretix API call in case the user information is not available in the in-memory store.


### Program notifications

Is a service to push the programme notification to Discord. Pretalx API is used to fetch the programme information, and `config.toml` holds information about livestream URLs.

### Organizers extension
A set of commands that are available only for organizers that are allowing to get statistics about the Discord server.

## Setup
### Install Python, Pipenv, Pyenv (Ubuntu)
```shell
# dependencies of readline, sqlite3, ctypes
sudo apt install libreadline-dev libsqlite3-dev lzma libbz2-dev liblzma-dev

# python, pip
sudo apt install python3 python3-pip

# pyenv
curl https://pyenv.run | bash
pyenv install 3.11.4

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
. ~/.bashrc

# pipenv
python3 -m pip install pipenv
```

### Clone repo, install dependencies, run tests
```shell
# clone repo, install dependencies
git clone https://github.com/EuroPython/discord europython-discord/
cd europython-discord

# install dependencies
python3 -m pipenv install --dev

# run tests
python3 -m pipenv run pytest .
```

### Configuration
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
