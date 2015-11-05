class ConnectionSendError(Exception):
    pass


class UnknownStrategyError(Exception):
    pass


class HandlerProcessingError(Exception):
    pass


class RouterProcessingError(Exception):
    pass


#-------------------------------------------
# this exception is raised when specific method
# is defined but there is no actual implementation.
#
class NotImplementedError(Exception):
    pass
