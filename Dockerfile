FROM python:3.11.4-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* var/log/*

USER bot
WORKDIR /home/bot

RUN python -m pip install --upgrade --user pip --no-cache-dir
RUN python -m pip install pipenv --user --no-cache-dir

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=bot:bot Pipfile Pipfile.lock ./
COPY --chown=bot:bot EuroPythonBot ./EuroPythonBot

RUN python -m pipenv sync
ENTRYPOINT ["pipenv", "run", "python", "EuroPython/bot.py"]
