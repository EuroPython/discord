# Europython 2023 Discord Bot

Make sure to configure the bot by using `config.toml.sample`
and to rename it to `config.toml` adding the required information:
* Server ID/Guild (`int`): that you can get by right-clicking the server Icon on discord,
* registration(help) channel ID (`int`): that you can get by right-clicking the channel on discord,
* online/inperson roles (`str`): that you need to define in the server settings.

## Run the bot
```shell
pipenv run python EuroPythonBot/bot.py
```

```shell
docker build -t discord_bot .
docker run -it -e DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN -e PRETIX_TOKEN=$PRETIX_TOKEN discord_bot
```
