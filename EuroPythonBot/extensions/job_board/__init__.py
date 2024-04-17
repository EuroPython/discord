"""Extension for posting in job board forum."""
import csv
import logging
from pathlib import Path

import aiofiles
import attrs
import discord
from discord.ext import commands

import configuration

_logger = logging.getLogger(f"bot.{__name__}")


async def setup(bot: commands.Bot) -> None:
    """Set up the organisers extension."""
    config = configuration.Config()
    await bot.add_cog(JobBoard(bot=bot, config=config))


@attrs.define
class JobBoard(commands.Cog):
    """Set up the job board extension."""

    _bot: commands.Bot
    _config: configuration.Config

    @commands.Cog.listener()
    async def on_ready(self):
        """Send jobs from csv file to job_board channel."""
        # get discord guild and channel
        self.guild = self._bot.get_guild(self._config.GUILD)
        self.channel = self._bot.get_channel(self._config.JOB_BOARD_CHANNEL_ID)

        # get set of already posted jobs
        self.posted_jobs_file = "./posted_jobs.txt"
        self.posted_jobs_set = self.load_posted_jobs()

        # read jobs from csv file (exported from google form)
        job_list = self.get_job_positions_from_csv(
            filename="Job Posts 2024 (Antworten) - Formularantworten 2.csv",
        )

        for job in job_list:
            key, name, content, thread_messages, file = self.prepare_job_post(job)
            if key not in self.posted_jobs_set:
                _logger.info(f"Posting new job: {key}")
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
                for thread_message in thread_messages:
                    await thread_with_message.thread.send(thread_message)

                # add key to posted_jobs_set and file
                self.posted_jobs_set.add(key)
                async with aiofiles.open(self.posted_jobs_file, mode="a") as f:
                    await f.write(f"{key}\n")
            else:
                _logger.info(f"Job already posted: {key}")

    def load_posted_jobs(self) -> set:
        """Load already posted jobs from txt file."""
        with open(self.posted_jobs_file, "r") as f:
            return set([reg.strip() for reg in f.readlines()])

    def get_job_positions_from_csv(self, filename: str) -> list:
        """Read csv file from google forms export."""
        path = Path(__file__).resolve().parent
        with open(file=path / filename, mode="r") as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # skip header row
            return [row for row in csv_reader]

    def prepare_job_post(self, job: list) -> tuple[str, str, str, list, discord.File | None]:
        """Prepare the job post."""
        # get values from job list
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
        key = f"{timestamp};{author};{job_title}"

        name = f"{company_name} is hiring: {job_title}"
        content = f"**Job location:** {job_location}\n" f"**Job description:**\n{job_description}"
        thread_messages = [
            f"**Duties and responsibilities:**\n{duties_and_responsibilities}",
            f"**Appreciated qualification and experience:**\n{qualifications}",
        ]
        if additional_info:
            thread_messages.append(f"**Additional info:**\n{additional_info}")
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

        file = None
        if job_picture:
            path = Path(__file__).resolve().parent
            filename = f"{company_name}.png"
            file = discord.File(path / "pictures" / filename, filename=filename)

        return key, name, content, thread_messages, file
