from enum import Enum

class TicketRole(Enum):
    VOLUNTEER = "volunteer"
    SPEAKER = "speaker"
    ATTENDENT = "attendent"
    REMOTE = "remote"
    # TODO - decide on roles

class TicketValidationError(Exception):
    pass
