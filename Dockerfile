FROM python:3.12-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* /var/log/*

WORKDIR /home/bot

RUN pip install uv
RUN rm -rf /home/bot/.cache

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --link --chown=bot:bot pyproject.toml ./
COPY --link --chown=bot:bot requirements.lock ./
COPY --link --chown=bot:bot PyConESBot ./PyConESBot

RUN uv pip install --system --no-cache -r requirements.lock && \
    rm -rf /home/bot/.cache

USER bot
ENTRYPOINT ["python", "PyConESBot/bot.py"]
