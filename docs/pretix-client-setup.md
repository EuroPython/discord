# Pretix Client Setup

The bot configuration contains multiple Pretix-related components:

* Environment variable `PRETIX_TOKEN`
* Configuration section `[registration]`

## Pretix Mock

If you don't have access to a real Pretix instance (or you prefer a small test instance), you can use
the script [scripts/pretix-mock.py](/scripts/pretix-mock.py).

### Run `pretix-mock.py`

The script has no dependencies. Simply choose an available port and run it in a separate terminal:

```shell
python scripts/pretix-mock.py --port 8080
```

This will host an HTTP server on `http://localhost:8080`.

### Configure the bot

Set the environment variable `PRETIX_TOKEN` to any string:

```shell
# macOS, Linux
export PRETIX_TOKEN="pretix-mock-token"

# Windows
$env:PRETIX_TOKEN = 'pretix-mock-token'
```

You can use the configuration values from [test-config.toml](/test-config.toml).
Make sure the entry `pretix_base_url` matches the port of your mock:
If you use `python pretix-mock.py --port 8888`, set `pretix_base_url` to `http://localhost:8888`.

## Real Pretix Instance

If you want to use a real Pretix instance, make sure the `[configuration]` section in your bot
configuration file matches the Pretix items and item variations.

Set the environment variable `PRETIX_TOKEN` to your access token, and the configuration entry
`pretix_base_url` to the base URL of your Pretix instance's API.
It typically looks like this:

```text
https://pretix.eu/api/v1/organizers/<organization>/events/<event>
```
