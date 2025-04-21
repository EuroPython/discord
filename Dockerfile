FROM python:3.11.4-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* /var/log/*

USER bot
WORKDIR /home/bot

ENV PATH="/home/bot/.local/bin:/home/bot/.venv/bin:$PATH"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pip install --upgrade --user pip && rm -rf /home/bot/.cache
RUN pip install poetry && rm -rf /home/bot/.cache
RUN rm -rf /home/bot/.cache

COPY --chown=bot:bot pyproject.toml poetry.lock ./
COPY --chown=bot:bot discord_bot ./discord_bot

RUN poetry install --no-root && \
    rm -rf /home/bot/.cache

ENTRYPOINT ["poetry", "run", "python", "discord_bot/bot.py"]
