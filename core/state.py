from enum import Enum, auto


class JarvisState(Enum):

    ##################################################
    # CORE STATES
    ##################################################

    STARTING = auto()

    IDLE = auto()

    LISTENING = auto()

    THINKING = auto()

    EXECUTING = auto()

    SPEAKING = auto()

    ##################################################
    # SYSTEM STATES
    ##################################################

    LOADING = auto()

    READY = auto()

    PAUSED = auto()

    ERROR = auto()

    SHUTDOWN = auto()