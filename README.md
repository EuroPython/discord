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

## Screenshots
### Registration Channel:
![Registration Channel](./img/registration-channel.png)

### Registration Form:
![Registration Form](./img/registration-form.png)

### Programme Notification:
![Programme Notification](./img/programme-notification.png)

## Configuration

All configuration is server-agnostic. You can set up your own Discord server and use the included configuration.

Arguments and environment variables:

* Argument `--config-file`: Path to .toml configuration file
* Environment variable `DISCORD_BOT_TOKEN`: Discord bot auth token (with Admin and `GUILD_MEMBERS` privileges)
* Environment variable `PRETIX_TOKEN`: Pretix access token (preferably read-only)

Included example configuration files:

* [`prod-config.toml`](./prod-config.toml) or [`test-config.toml`](./test-config.toml): Prod/Test configuration
* [`test-livestreams.toml`](./test-livestreams.toml): Test livestream URL configuration

Used cache and log files (will be created if necessary):

* `pretix_cache.json`: Local cache of Pretix ticket data
* `registered_log.txt`: Log of registered users
* `schedule_cache.json`: Local cache of [programapi](https://github.com/europython/programapi) schedule

## Setup
### Quickstart using `pip`

If you just want to try the bot and skip the development setup, you can use `pip` (requires Python >= 3.11):

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

### Full Development Setup

* Install `uv` as documented [here](https://docs.astral.sh/uv/getting-started/installation/).
* Run `uv sync --dev` to create/update a virtual environment with all dependencies according to [`uv.lock`](./uv.lock).
* Run `. .venv/bin/activate` (Windows: `.venv/Scripts/activate`) to activate the virtual environment
* Run `pre-commit install` to install the [pre-commit](https://pre-commit.com/) hooks.
* Run `pre-commit run --all-files` to verify your setup. All checks should pass.

To run the bot, use the following:

```shell
# set environment variables
export DISCORD_BOT_TOKEN=...  # Windows: $env:DISCORD_BOT_TOKEN = '...'
export PRETIX_TOKEN=...  # Windows: $env:PRETIX_TOKEN = '...'

# run the bot with a given config file
run-bot --config your-config-file.toml
```

#### Working with `uv`

This is a list of useful commands when working with `uv`.
Please refer to the [uv documentation](https://docs.astral.sh/uv) or `uv help` for details.

```shell
# activate uv-generated virtual environment ("venv")
. .venv/bin/activate  # Windows: '.venv/Scripts/activate'

# create/synchronize venv based on uv.lock file
uv sync
uv sync --dev  # include dev dependencies

# execute command inside uv-generated venv (can be skipped if venv is activated)
uv run [command]

# add package
uv add [package]
uv add --dev [package]  # as dev dependency

# upgrade packages
uv lock --upgrade

# remove package
uv remove [package]
```

### Development tools

* Run everything: `pre-commit run --all-files`
* Format code: `ruff format`
* Check code format: `ruff format --check`
* Fix imports: `ruff check --select I001,F401 --fix`
* Check code style: `ruff check .`
* Run tests: `pytest`

### Deployment

The bot is deployed on a VPS using a GitHub Action.
It uses Ansible to configure the VPS, and Docker Compose to run the bot.

Related files:

* [.github/workflows/deploy.yml](./.github/workflows/deploy.yml): The GitHub Action
* [ansible/deploy-playbook.yml](./ansible/deploy-playbook.yml): The Ansible Playbook
* [Dockerfile](./Dockerfile): The Docker container recipe
* [compose.yaml](./compose.yaml): The Docker Compose recipe
* [prod-config.toml](./prod-config.toml): The Prod bot configuration
