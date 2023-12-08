FROM python:3.11.4-slim

RUN groupadd --gid 1000 ec2-user && \
    useradd --uid 1000 --gid ec2-user ec2-user --create-home && \
    rm -rf /var/cache/* var/log/*

USER bot
WORKDIR /home/bot

RUN pip install --upgrade --user pip && rm -rf /home/ec2-user/.cache
RUN pip install --user pipenv && rm -rf /home/ec2-user/.cache
RUN rm -rf /home/ec2-user/.cache

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=ec2-user:ec2-user Pipfile Pipfile.lock ./
COPY --chown=ec2-user:ec2-user EuroPythonBot ./EuroPythonBot

RUN pipenv sync && \
    rm -rf /home/ec2-user/.cache

ENTRYPOINT ["pipenv", "run", "python", "EuroPythonBot/bot.py"]
