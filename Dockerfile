FROM python:3.11.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* /var/log/*

USER bot
WORKDIR /home/bot

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=bot:bot pyproject.toml uv.lock ./
COPY --chown=bot:bot src ./src

RUN uv sync

ENTRYPOINT ["uv", "run", "run-bot", "--config-file", "prod-config.toml"]
