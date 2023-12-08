# Europython 2023 Discord Bot

## Run the bot
Add `.secrets` file to the root of the repository with the following content:

```shell
DISCORD_BOT_TOKEN=<EuroPythonTestBotToken_from_1Password>
PRETIX_TOKEN=<PretixStagingToken_from_1Password>
````
After you have added the `.secrets` file, you can run the bot with the following command:
```shell
pipenv run EuroPythonBot/bot.py
```
or with docker:
```shell
docker build --tag discord_bot .
docker run -it --env DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN \
 --env PRETIX_TOKEN=$PRETIX_TOKEN \
 --volume "$(pwd)"/registered_log.txt:/home/bot/registered_log.txt \
 --volume "$(pwd)"/discord/.secrets:/home/bot/EuroPythonBot/.secrets discord_bot
```
