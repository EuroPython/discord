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
### Quickstart using `pip`

This project uses [uv](https://github.com/astral-sh/uv) for managing dependencies.
If you just want to try the bot and skip all the development setup,
you can use `pip` instead of `uv` (requires Python >= 3.11):

```shell
# create and activate virtual environment (optional, but recommended)
python -m venv .venv
. .venv/bin/activate  # Windows: '.venv/Scripts/activate'

# install this package
pip install .

# run the bot
run-bot
```

### Development setup using `uv`

Install `uv` as documented [here](https://docs.astral.sh/uv/getting-started/installation/), then
create/update virtual environment with all dependencies according to [`uv.lock`](./uv.lock) 
with `uv sync --dev`.

If required, `uv` will download the required Python version, as specified in 
[`.python-version`](./.python-version).

### Using `uv`

This is a summary of useful `uv` commands.
Please refer to the [uv documentation](https://docs.astral.sh/uv) or `uv help` for details.

```shell
# generate .venv/ from uv.lock
uv sync
uv sync --dev  # include dev dependencies

# activate uv-generated venv
. .venv/bin/activate  # Windows: '.venv/Scripts/activate'

# reset all packages to versions pinned in uv.lock
uv sync
uv sync --dev  # include dev dependencies

# add package
uv add package
uv add --dev package  # install as dev dependency

# upgrade packages
uv lock --upgrade

# remove package
uv remove package
```

### Development tools

* Format code: `uv run --dev ruff format`
* Check code format: `uv run --dev ruff format --check`
* Sort imports: `uv run --dev ruff check --select I001 --fix`
* Check import order: `uv run --dev ruff check --select I001`
* Check code style: `uv run --dev flake8 .`
* Run tests: `uv run --dev pytest .`

### Configuration

Create `config.local.toml` file in EuroPythonBot directory, it would be used instead of `config.toml` if exists.

Add `.secrets` file to the root of the repository with the following content:

```shell
DISCORD_BOT_TOKEN=<EuroPythonTestBotToken_from_1Password>
PRETIX_TOKEN=<PretixStagingToken_from_1Password>
````

After you have added the `.secrets` file, you can run the bot with the following command:

```shell
run-bot
```

or with docker:

```shell
docker build --tag discord_bot .
docker run --interactive --tty --env DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN --env PRETIX_TOKEN=$PRETIX_TOKEN discord_bot
```
