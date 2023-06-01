"""Discord Registration Bot"""
import logging
from typing import Tuple
import sqlite3
import os

import discord
import requests



# CONSTANTS
SERVER_ID = 955933777706762280
ATTENDEE_ROLE_NAME =  "Attendee"
SPEAKER_ROLE_NAME = "Speaker"
LOG_FILE = "discord.log"
DB_PATH = "db/registration_bot.db"
REGISTER_COMMAND = "!register"

logger = logging.getLogger()


def validate_user_input(
    ticket_id: str, name: str
) -> Tuple[bool, bool, str, str]:
    """
    Validate the user input.
    
    Args:
        ticket_id (str): user input for ticket ID (booking reference)
        name (str): user input for name (usually 'Fistname Lastname')
    
    Returns:
        bool: valid_request
        bool: is_speaker
        str: hint, returned from request
        str: comment, for additional info such as issues with the request
    
    """
    # default variables
    valid_request = False
    hint = "Something went wrong. Please try again"
    comment = ""

    # API request to validate ticket
    url = "http://78.94.223.124:15748/tickets/validate_name"
    json = {
        "ticket_id": ticket_id,
        "name": name
    }
    r = requests.post(url, json=json)
    data = r.json()
    if data:
        valid_request = data["is_attendee"]
        hint = data["hint"]
        is_speaker = data["is_speaker"]
        
        if not valid_request:
            comment = f"Ticket ID / Name mismatch: {hint}"
    else:
        comment = (
            f"Ticket checking returned status code: {r.status_code}: {r.text}"
        )
        logger.warning(comment)

    return valid_request, is_speaker, hint, comment


class MyClient(discord.Client):
    def __init__(self, intents, db_path):
        super().__init__(intents=intents)
        self.server_id = SERVER_ID
        self.attendee_role_name = ATTENDEE_ROLE_NAME
        self.speaker_role_name = SPEAKER_ROLE_NAME
        # DB connection
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def save_request_to_DB(
        self, user_id, ticket_id, name, valid_request, is_speaker, comment
    ):
        """
        Insert and commit the request to the registration table in the DB.
        """
        valid = 1 if valid_request else 0

        # save validation request to DB
        self.cur.execute(
            """
            INSERT INTO registration
            (user_id, ticket_id, name, valid, is_speaker, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, ticket_id, name, valid, is_speaker, comment)
        )
        self.con.commit()
        logger.info(
            f"Inserted user_id={user_id}, ticket_id={ticket_id}, "
            f"name={name}, valid={valid_request} into DB."
            )

    async def on_ready(self):
        logger.info(f"Logged on as {self.user}!")

    async def on_member_join(self, member):
        """send private welcome message with instructions"""
        try:
            await member.send(
                "Hello there! Welcome to the PyCon/PyData Berlin Conference. "
                f"Please reply with '{REGISTER_COMMAND}' to start the "
                "ticket validation process so you can access the conference's "
                "Discord channels."
            )
        except discord.errors.Forbidden:
            logger.info(f"Not allowed to send private DM to member {member}")

    async def _answer_in_public(self, message):
        """send public response if messaged with mention"""
        public_channels_answer = (
            "Hello! Please send me a private message with "
            f"'{REGISTER_COMMAND}' to start the ticket authorization process."
        )
        await message.reply(public_channels_answer, mention_author=True)

    async def _assign_role(self, user_id: int, role_name: str) -> None:
        """
        Assign the user with user_id the role `role_name`.

        Args:
            user_id (int): user ID
            role_name (str): name of the role that the user should be assigned
        """
        guild = self.get_guild(self.server_id)
        if guild:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                member = guild.get_member(user_id)
                if member:
                    await member.add_roles(role)
                else:
                    logger.error(f"user with ID {user_id} not found")
            else:
                logger.error(f"role {role_name} not found.")
        else:
            logger.error(f"guild for {self.server_id} not found")

    async def on_message(self, message):
        """
        - Answer to direct mentions in channels with registration process
            instructions. 
        - Check for `REGISTER_COMMAND` to start the registration process.
        """
        # get user_id from message
        user_id = message.author.id

        if message.author.bot:
            # bot should not reply to itself
            return

        if not isinstance(message.channel, discord.DMChannel):
            # if bot (user) is mentioned in message
            if self.user in message.mentions:
                # reply with public message
                await self._answer_in_public(message)
            return

        if message.content.startswith(f"{REGISTER_COMMAND}"):
            # start registration process
            def check(answer):
                """check for user and direct message."""
                return answer.author.id == message.author.id and isinstance(
                    message.channel, discord.DMChannel
                )

            # ask user for ticket id
            await message.author.send(
                "Hello there! It's great to see you here. We hope you are "
                "doing well. To help you access the conference's Discord "
                "channels, we kindly request you to share your ticket ID "
                "(Booking reference) with us. You can find it in your "
                "registration email. Please provide your ticket ID (e.g. "
                "something like 'CLST-1')."
            )
            ticket_msg = await self.wait_for("message", check=check)
            ticket_id = ticket_msg.content

            # ask the user for their name
            await message.author.send(
                "Thank you. Please provide your full name (as printed on your "
                " ticket, usually 'Firstname Lastname')."
            )
            name_msg = await self.wait_for("message", check=check)
            name = name_msg.content

            # validate user input
            valid_request, is_speaker, hint, comment = validate_user_input(
                ticket_id, name
            )

            # check if ticket ID was used before
            used_ticket_ids = [
                row[0] for row in self.cur.execute(
                    "SELECT DISTINCT ticket_id FROM registration WHERE valid=1"
                ).fetchall()
            ]
            if valid_request and ticket_id in used_ticket_ids:
                comment = "Ticket ID already used!"
                logger.warning(
                    f"Ticket ID '{ticket_id}' for name '{name}' "
                    f"entered by user_id '{user_id}' was used before!"
                )
                valid_request = False

                self.save_request_to_DB(
                    user_id,
                    ticket_id,
                    name,
                    valid_request,
                    is_speaker,
                    comment
                )

                await message.author.send(
                    "Sorry, the ticket ID was already used. Please contact us "
                    f"in the #help channel or try the '{REGISTER_COMMAND}' "
                    f"command again: {hint}"
                )
                return

            if not valid_request:
                # invalid input: Ticket ID / name does not match
                logger.warning(
                    f"Invalid ticket ID '{ticket_id}' for name '{name}' "
                    f"entered by user_id '{user_id}'."
                )

                self.save_request_to_DB(
                    user_id,
                    ticket_id,
                    name,
                    valid_request,
                    is_speaker,
                    comment
                )

                await message.author.send(
                    "Sorry, the ticket ID does not correspond to the name. "
                    f"Please call the '{REGISTER_COMMAND}' command again: "
                    f"{hint}"
                )
                return

            # valid input
            logger.info(
                f"Valid ticket ID '{ticket_id}' for name '{name}' "
                f"entered by user_id '{user_id}'. Assigning 'Attendee' role..."
            )
            # assign role(s) to the user_id
            await self._assign_role(user_id, self.attendee_role_name)
            assigned_roles_str =  f"'{self.attendee_role_name}' role"
            if is_speaker:
                await self._assign_role(user_id, self.speaker_role_name)
                assigned_roles_str = (
                    f"'{self.attendee_role_name}' and "
                    f"'{self.speaker_role_name}' roles"
                )

            self.save_request_to_DB(
                    user_id,
                    ticket_id,
                    name,
                    valid_request,
                    is_speaker,
                    comment
                )
            logger.info(
                f"Valid ticket ID '{ticket_id}' for name '{name}' "
                f"entered by user_id '{user_id}'. {assigned_roles_str} "
                "assigned."
            )
            # send success message to user
            await message.author.send(
                "Great news! We have verified the credentials you provided, "
                "and everything checks out. You were assigned the "
                f"{assigned_roles_str} and now have access to conference's "
                "Discord channels. "
            )
            return


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

    # configure discord intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # start discord client
    client = MyClient(intents=intents, db_path=DB_PATH)
    client.run(
        os.environ.get("DISCORD_REGISTRATION_BOT_TOKEN", ""),
        log_handler=file_handler
    )
