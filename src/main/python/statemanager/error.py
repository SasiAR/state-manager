class NoDbSessionAttachedError(Exception):
    pass


class NoInitialStateDefinedError(Exception):
    pass


class NextStateNotDefinedError(Exception):
    pass


class NoStateDefinedError(Exception):
    pass


class NoWorkflowDefined(Exception):
    pass