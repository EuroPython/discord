FROM python:3.12-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* /var/log/*

USER bot
WORKDIR /home/bot

RUN pip install uv
RUN rm -rf /home/bot/.cache

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=bot:bot requirements.lock ./
COPY --chown=bot:bot PyConESBot ./PyConESBot

RUN uv pip install --no-cache --system -r requirements.lock && \
    rm -rf /home/bot/.cache

ENTRYPOINT ["python", "PyConESBot/bot.py"]
