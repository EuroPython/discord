"""Extension for posting in job board forum."""

from __future__ import annotations

import csv
import logging

# import random
from pathlib import Path

import aiofiles
import attrs
import discord
from discord.ext import commands

from discord_bot import configuration

_logger = logging.getLogger(f"bot.{__name__}")


async def setup(bot: commands.Bot) -> None:
    """Set up the job_board extension."""
    config = configuration.Config()
    await bot.add_cog(JobBoard(bot=bot, config=config))


@attrs.define
class JobBoard(commands.Cog):
    """Set up the job board extension."""

    _bot: commands.Bot
    _config: configuration.Config

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Send jobs from csv file to job_board channel."""
        # get discord guild and channel
        self.guild = self._bot.get_guild(self._config.GUILD)
        self.channel = self._bot.get_channel(self._config.JOB_BOARD_CHANNEL_ID)
        # set to True for testing to delete the threads automatically after posting
        self.JOB_BOARD_TESTING = self._config.JOB_BOARD_TESTING

        # get set of already posted jobs
        self.posted_jobs_file = "./posted_jobs.txt"
        self.posted_jobs_set = self.load_posted_jobs()

        # read jobs from csv file (exported from google form)
        job_list = self.get_job_positions_from_csv(filename="jobs.csv")

        threads = []  # list of threads to delete when testing

        # shuffle job_list for random post order
        # random.seed(42)
        # random.shuffle(job_list)
        for job in reversed(job_list):
            key, name, content, thread_messages, file = self.prepare_job_post(job)
            if key not in self.posted_jobs_set:
                msg = f"Posting new job: {key}"
                _logger.info(msg)
                if file:
                    thread_with_message = await self.channel.create_thread(
                        name=name,
                        content=content,
                        file=file,
                    )
                else:
                    thread_with_message = await self.channel.create_thread(
                        name=name,
                        content=content,
                    )
                # get thread and add to threads list
                thread = thread_with_message.thread
                threads.append(thread)

                for thread_message in thread_messages:
                    await thread.send(thread_message)

                # add key to posted_jobs_set and file
                self.posted_jobs_set.add(key)
                async with aiofiles.open(self.posted_jobs_file, mode="a") as f:
                    await f.write(f"{key}\n")
            else:
                msg = f"Job already posted: {key}"
                _logger.info(msg)

        if self.JOB_BOARD_TESTING:
            for thread in threads:
                await thread.delete()

    def load_posted_jobs(self) -> set:
        """Load already posted jobs from txt file."""
        with open(self.posted_jobs_file) as f:  # noqa: PTH123
            return {reg.strip() for reg in f}

    def get_job_positions_from_csv(self, filename: str) -> list:
        """Read csv file from google forms export."""
        path = Path(__file__).resolve().parent
        with open(file=path / filename) as f:  # noqa: PTH123
            csv_reader = csv.reader(f)
            next(csv_reader)  # skip header row
            return list(csv_reader)

    def format_thread_message(self, title: str, message: str) -> list:
        """Split thread messages that are too long for discord to handle into multiple messages."""
        message_limit = 2000
        if len(title) + len(message) + 10 > message_limit:
            split_message = [message[i : i + message_limit] for i in range(0, len(message), message_limit)]
            return [f"**{title}:**\n", *split_message]
        return [f"**{title}:**\n{message}"]

    def prepare_job_post(
        self,
        job: list,
    ) -> tuple[str, str, str, list, discord.File | None]:
        """Prepare the job post."""
        # get values from job columns
        timestamp = job[0]
        author = job[1]
        job_title = job[2].strip()
        company_name = job[3].strip()
        job_location = job[4]
        deadline = job[5]
        job_description = job[6]
        duties_and_responsibilities = job[7]
        qualifications = job[8]
        additional_info = job[9]  # optional
        contact_person_name = job[10]
        contact_person_email = job[11]
        url = job[12]
        job_picture = job[13]

        # create unique key per job post
        key = f"{timestamp};{author};{job_title};{company_name}"

        name = f"{company_name} is hiring: {job_title}"[:100]
        content = f"**Job title:** {job_title}\n**Job location:** {job_location}"

        thread_messages = []
        thread_messages.extend(self.format_thread_message("Job description", job_description))
        thread_messages.extend(
            self.format_thread_message("Duties and responsibilities", duties_and_responsibilities),
        )
        thread_messages.extend(
            self.format_thread_message("Appreciated qualification and experience", qualifications),
        )

        if additional_info:
            thread_messages.extend(self.format_thread_message("Additional info", additional_info))
        if deadline:
            thread_messages.append(f"**Application deadline:**\n{deadline}")

        if contact_person_name or contact_person_email:
            contact = "**Contact:** "
            if contact_person_name and contact_person_email:
                contact += f"{contact_person_name} ({contact_person_email})."
            elif contact_person_name:
                contact += f"{contact_person_name}."
            elif contact_person_email:
                contact += f"{contact_person_email}."
            thread_messages.append(contact)
        if url:
            thread_messages.append(f"**More info at:** {url}")

        companies_with_different_pictures = ["GetYourGuide"]

        file = None
        if job_picture:
            path = Path(__file__).resolve().parent
            filename = f"{company_name}.png"
            if company_name in companies_with_different_pictures:
                # replace special characters in job_title
                job_title_r = job_title.replace("/", "_")
                job_title_r = job_title_r.replace(":", "_")
                filename = f"{company_name}-{job_title_r}.png"
            file = discord.File(path / "pictures" / filename, filename=filename)

        return key, name, content, thread_messages, file
