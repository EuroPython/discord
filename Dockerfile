FROM python:3.11.4-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* var/log/*

USER bot
WORKDIR /home/bot

RUN pip install --upgrade --user pip && rm -rf /home/bot/.cache
RUN pip install --user poetry && rm -rf /home/bot/.cache
RUN rm -rf /home/bot/.cache

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=bot:bot pyproject.toml poetry.lock ./
COPY --chown=bot:bot discord_bot ./discord_bot

RUN python -m venv /home/bot/venv && \
    . /home/bot/venv/bin/activate && \
    poetry install && \
    rm -rf /home/bot/.cache

ENTRYPOINT ["/home/bot/venv/bin/python", "discord_bot/bot.py"]
