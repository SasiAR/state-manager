from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from statemanager.error import NoDbSessionAttachedError
from sqlalchemy.orm import sessionmaker


__state_session_factory = None


def set_session_factory(sm: sessionmaker) -> None:
    global __state_session_factory
    __state_session_factory = sm


def current_session() -> Session:
    if __state_session_factory is None:
        raise NoDbSessionAttachedError("DB Session is not attached, "
                                       "call initilaize in statemanager with db session factory")

    return scoped_session(__state_session_factory)
