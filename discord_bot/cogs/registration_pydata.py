"""Registration for PyData."""

# ruff: noqa: D101, D107
from discord.ext import commands

from discord_bot.cogs.registration import Registration, RegistrationButton, RegistrationForm, RegistrationView
from discord_bot.configuration import Config

# from discord_bot.error import AlreadyRegisteredError, NotFoundError
# from discord_bot.channel_logging import log_to_channel
# from discord_bot.ticket_connector import TicketOrder


config = Config()
# order_ins = TicketOrder()

# CHANGE_NICKNAME = False

EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"

# _logger = logging.getLogger(f"bot.{__name__}")


class RegistrationButtonPyData(RegistrationButton):
    def __init__(
        self,
        registration_form: RegistrationForm,  # noqa: ARG002
    ) -> None:
        super().__init__(registration_form=RegistrationFormPyData)


class RegistrationFormPyData(RegistrationForm):
    def __init__(self) -> None:
        title = f"{config.CONFERENCE_NAME} Registration"
        super().__init__(title=title)


class RegistrationViewPyData(RegistrationView):
    def __init__(self) -> None:
        super().__init__(registration_button=RegistrationButtonPyData, registration_form=RegistrationFormPyData)


class RegistrationPyData(Registration, commands.Cog):
    def __init__(self, bot) -> None:  # noqa: ANN001
        super().__init__(bot, registration_view=RegistrationViewPyData)
        self._title = f"Welcome to {config.CONFERENCE_NAME} on Discord! 🎉🐍"
        self._desc = (
            "Follow these steps to complete your registration:\n\n"
            f'1️⃣ Click on the green "Register Here {EMOJI_POINT}" button.\n\n'
            '2️⃣ Fill in the "ticket/order ID" in the format "XXXXX", e.g. "AB1CD") and '
            "your full name (as printed on your ticket PDF). The ticket/order ID can also be found on your ticket PDF."
            "Trouble finding the infos? Check your emails from tickets@pydata-berlin.org again."
            # "You can find the information also in your confirmation email from "
            # f'tickets@pydata-berlin.org with the subject: '
            # '"[Action required] Ticket for {config.CONFERENCE_NAME}".\n\n'
            '3️⃣ Click "Submit". We\'ll verify your ticket and give you your role(s) based on '
            "your ticket type so you can see the conference channels.\n\n"
            "Your registration was successful if you can see the conference channels under the categories "
            f"'{config.CONFERENCE_YEAR}_CONFERENCE' and '{config.CONFERENCE_YEAR}_ROOMS'.\n\n"
            "Experiencing trouble? Ask for help in the #registration-help channel or from a "
            f"volunteer (look for the {config.VOLUNTEER_SHIRT_COLOR} t-shirts) at the conference.\n\n"
            f"See you at {config.CONFERENCE_NAME}! 🐍💻🎉"
        )
