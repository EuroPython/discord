"""Registration for PyData."""
from discord.ext import commands

from cogs.registration import (
    Registration,
    RegistrationButton,
    RegistrationForm,
    RegistrationView,
)

# from configuration import Config
# from error import AlreadyRegisteredError, NotFoundError
# from helpers.channel_logging import log_to_channel
# from helpers.tito_connector import TitoOrder


# config = Config()
# order_ins = TitoOrder()

# CHANGE_NICKNAME = False

EMOJI_POINT = "\N{WHITE LEFT POINTING BACKHAND INDEX}"

# _logger = logging.getLogger(f"bot.{__name__}")


# TODO(dan): make pydata subclass with changes


class RegistrationButtonPyData(RegistrationButton):
    def __init__(
        self,
        registration_form: RegistrationForm,
    ):
        super().__init__(registration_form=RegistrationFormPyData)


class RegistrationFormPyData(RegistrationForm):
    def __init__(self):
        super().__init__(title="PyConDE/PyData Berlin 2024 Registration")


class RegistrationViewPyData(RegistrationView):
    def __init__(self):
        super().__init__(
            registration_button=RegistrationButtonPyData, registration_form=RegistrationFormPyData
        )


class RegistrationPyData(Registration, commands.Cog):
    def __init__(self, bot):
        super().__init__(bot, registration_view=RegistrationViewPyData)
        self._title = "Welcome to PyConDE / PyData Berlin 2024 on Discord! 🎉🐍"
        # TODO(dan): update text
        self._desc = (
            "Follow these steps to complete your registration:\n\n"
            f'1️⃣ Click on the green "Register Here {EMOJI_POINT}" button.\n\n'
            '2️⃣ Fill in the "Order" (found by clicking the order URL in your confirmation '
            'email from support@pretix.eu with the Subject: Your order: XXXX) and "Full Name" '
            "(as printed on your ticket/badge).\n\n"
            '3️⃣ Click "Submit". We\'ll verify your ticket and give you your role based on '
            "your ticket type.\n\n"
            "Experiencing trouble? Ask for help in the registration-help channel or from a "
            "volunteer in yellow t-shirt at the conference.\n\n"
            "See you on the server! 🐍💻🎉"
        )
