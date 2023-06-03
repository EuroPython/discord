import string
from typing import List, Optional

from model import TicketRole, TicketValidationError


def get_ticket_roles_from_message_with_ticket_id(
    message, screen_name
) -> Optional[List[TicketRole]]:
    """accepts any string message and a discord screen name"""
    # TODO - this is just a dummy
    # a real function would also consider the screen name to decide
    # if a ticket is valid
    if message:
        translator = str.maketrans("", "", string.punctuation)
        message_words = message.translate(translator).split()
        if "V001" in message_words:
            # This is how to communicate a ticket error
            if False:
                raise TicketValidationError(
                    "Check that your screen name matches the ticket"
                )
            return [TicketRole.VOLUNTEER, TicketRole.ATTENDENT]
        if "T001" in message_words:
            return [TicketRole.ATTENDENT]
        if "S001" in message_words:
            return [TicketRole.ATTENDENT, TicketRole.SPEAKER]
