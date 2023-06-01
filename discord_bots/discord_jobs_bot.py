import datetime
import logging
import os

import pandas as pd

import discord
from discord.ext import tasks

# GLOBAL VARIABLES
# SERVER_ID = 955933777706762280
JOBS_CHANNEL_ID = 1094579305683628032  # job-board channel
LOG_FILE = "discord_jobs.log"
JOB_URLS_CSV_PATH = "job_urls.csv"

# when to post the jobs
ANNOUNCEMENT_HOUR = 13
ANNOUNCEMENT_MINUTE = 0

DAILY_ANNOUNCEMENT_TIME = datetime.time(
    hour=ANNOUNCEMENT_HOUR-2,  # UTC-2 for Berlin time zone
    minute=ANNOUNCEMENT_MINUTE,
    tzinfo=datetime.timezone.utc
)

# TEST_CONFERENCE_DAY = datetime.date(2023, 4, 14)
FIRST_CONFERENCE_DAY = datetime.date(2023, 4, 17)
SECOND_CONFERENCE_DAY = datetime.date(2023, 4, 18)
THIRD_CONFERENCE_DAY = datetime.date(2023, 4, 19)

logger = logging.getLogger()

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f"Logged on as {self.user}!")

    def cog_unload(self) -> None:
        self.job_posting_task.cancel()

    async def setup_hook(self) -> None:
        self.job_posting_task.start()

    def _generate_posts(self, day: int) -> list[str]:
        logger.info(f"Generating job posts for day {day}")
        posts = []
        # read job csv
        df = pd.read_csv(JOB_URLS_CSV_PATH)

        # filter df by nth `day` (zero-based) -> get first, second, ...
        # posting per company
        df = df.groupby('company_name').nth(day)

        # create job posts,
        for i, r in df.iterrows():
            posts.append(
                f"{r['company_name']} is hiring a {r['job_title']}! "
                f"See https://2023.pycon.de/job-board/{i}/ for more info."
            )
        return posts

    async def send_job_posts(self, day: int) -> None:
        logger.info("Sending job posts...")
        channel = self.get_channel(JOBS_CHANNEL_ID)
        posts = self._generate_posts(day)
        for post in posts:
            await channel.send(post)  # type: ignore

    @tasks.loop(time=DAILY_ANNOUNCEMENT_TIME)  # times)
    async def job_posting_task(self):
        today = datetime.date.today()
        if today == FIRST_CONFERENCE_DAY:
            logger.info("First conference day")
            await self.send_job_posts(day=0)
        elif today == SECOND_CONFERENCE_DAY:
            logger.info("Second conference day")
            await self.send_job_posts(day=1)
        elif today == THIRD_CONFERENCE_DAY:
            logger.info("Third conference day")
            await self.send_job_posts(day=2)
        # elif today == TEST_CONFERENCE_DAY:
        #     logger.info("Test conference day")
        #     await self.send_job_posts(day=2)
        else:
            logger.info("Not a conference day. No job posts.")
            return

    @job_posting_task.before_loop
    async def before_job_posting_task(self):
        await self.wait_until_ready()


if __name__ == "__main__":
    # configure logging
    file_handler = logging.FileHandler(
        filename=LOG_FILE, encoding="utf-8", mode="a"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    
    client = MyClient(intents=discord.Intents.default())
    client.run(
        os.environ.get("DISCORD_JOB_BOT_TOKEN", ""),
        log_handler=file_handler
        
    )
