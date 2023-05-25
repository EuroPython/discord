from enum import Enum

class TicketRole(Enum):
    VOLUNTEER = "volunteer"
    SPEAKER = "speaker"
    ATTENDENT = "attendent"
    # TODO - decide on roles

class TicketValidationError(Exception):
    pass
