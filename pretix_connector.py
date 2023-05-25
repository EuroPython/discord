
from enum import Enum
import string
from typing import Optional, List


class TicketRole(Enum):
    VOLUNTEER = "volunteer"
    SPEAKER = "speaker"
    ATTENDENT = "attendent"
    # TODO - decide on roles


def get_ticket_roles_from_message_with_ticket_id(message, screen_name) -> Optional[List[TicketRole]]:
    """accepts any string message and a discord screen name"""
    # TODO - this is just a dummy
    # a real function would also consider the screen name to decide
    # if a ticket is valid
    if message:
        translator = str.maketrans("", "", string.punctuation)
        message_words = message.translate(translator).split()
        if "V001" in message_words:
            return [TicketRole.VOLUNTEER, TicketRole.ATTENDENT]
        if "T001" in message_words:
            return [TicketRole.ATTENDENT]
        if "S001" in message_words:
            return [TicketRole.ATTENDENT, TicketRole.SPEAKER]


