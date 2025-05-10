# Europython Discord

A suite of tools for managing the EuroPython Conference Discord server:

* [src/europython_discord](./src/europython_discord): Discord bot
* [scripts/configure-guild.py](./scripts/configure-guild.py): Configure channels and roles of a Discord server
* [scripts/export-members.py](./scripts/export-members.py): Export a list of all server members and their roles

The scripts work standalone and only require an Auth token. Please find more documentation in the respective files.

The bot has the following extensions ("Cogs"):

* Ping: To check if the bot is running, write `$ping` in any channel. The bot will respond with `Pong!`.
* Guild Statistics: As an organizer, write `$participants` in an organizer-only channel. The bot will respond with a list of roles, and the number of members per role.
* Registration: On startup, the bot posts a registration form. New users must register using their Pretix ticket data. On success, the bot assigns the appropriate roles.
* Programme Notifications: Before each session, the bot posts a session summary and updates the livestream URLs.

![registration_view.png](./img/registration_view.png)

## Configuration

All configuration is server-agnostic. You can set up your own Discord server and use the included configuration.

Configuration files:

* [`prod-config.toml`](./prod-config.toml) or [`test-config.toml`](./test-config.toml): Prod/Test configuration
* [`livestreams.toml`](./livestreams.toml): Livestream URL configuration

Arguments and environment variables:

* Argument `--config-file`: Path to .toml configuration file
* Environment variable `DISCORD_BOT_TOKEN`: Discord bot auth token (with Admin and `GUILD_MEMBERS` privileges)
* Environment variable `PRETIX_TOKEN`: Pretix access token (preferably read-only)

Files expected in the current directory (may be empty):

* `pretix_cache.json`: Local cache of Pretix ticket data
* `registered_log.txt`: Log of registered users
* `schedule.json`: Local cache of [programapi](https://github.com/europython/programapi) schedule

## Setup
### Quickstart using `pip`

This project uses [uv](https://github.com/astral-sh/uv) for managing dependencies.
If you just want to try the bot and skip the development setup,
you can use `pip` instead of `uv` (requires Python >= 3.11):

```shell
# create and activate virtual environment (optional, but recommended)
python -m venv .venv
. .venv/bin/activate  # Windows: .venv/Scripts/activate

# install this package (use '-e' for 'editable mode' if you plan to modify the code)
pip install .

# set environment variables
export DISCORD_BOT_TOKEN=...  # Windows: $env:DISCORD_BOT_TOKEN = '...'
export PRETIX_TOKEN=...  # Windows: $env:PRETIX_TOKEN = '...'

# run the bot with a given config file
run-bot --config your-config-file.toml
```

### Development setup using `uv`

Install `uv` as documented [here](https://docs.astral.sh/uv/getting-started/installation/), then run `uv sync --dev` to create/update a
virtual environment with all dependencies according to [`uv.lock`](./uv.lock).

If required, `uv` will download the required Python version, as specified in 
[`.python-version`](./.python-version).

To run the bot, use the following:

```shell
# set environment variables
export DISCORD_BOT_TOKEN=...  # Windows: $env:DISCORD_BOT_TOKEN = '...'
export PRETIX_TOKEN=...  # Windows: $env:PRETIX_TOKEN = '...'

# run the bot with a given config file
uv run run-bot --config your-config-file.toml
```

#### Useful `uv` commands

Please refer to the [uv documentation](https://docs.astral.sh/uv) or `uv help` for details.

```shell
# generate .venv/ from uv.lock
uv sync
uv sync --dev  # include dev dependencies

# activate uv-generated venv
. .venv/bin/activate  # Windows: '.venv/Scripts/activate'

# execute command inside uv-generated venv
uv run [command]

# reset all packages to versions pinned in uv.lock
uv sync
uv sync --dev  # include dev dependencies

# add package
uv add [package]
uv add --dev [package]  # install as dev dependency

# upgrade packages
uv lock --upgrade

# remove package
uv remove [package]
```

### Development tools

* Format code: `uv run --dev ruff format`
* Check code format: `uv run --dev ruff format --check`
* Sort imports: `uv run --dev ruff check --select I001 --fix`
* Check code style: `uv run --dev ruff check .`
* Run tests: `uv run --dev pytest .`

### Deployment

The bot is deployed on a VPS using a GitHub Action.
It uses Ansible to configure the VPS, and Docker Compose to run the bot.

Related files:

* [.github/workflows/deploy.yml](./.github/workflows/deploy.yml): The GitHub Action
* [ansible/deploy-playbook.yml](./ansible/deploy-playbook.yml): The Ansible Playbook
* [Dockerfile](./Dockerfile): The Docker container recipe
* [compose.yaml](./compose.yaml): The Docker Compose recipe
