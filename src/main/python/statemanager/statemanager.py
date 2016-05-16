from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import Session
from statemanager.statemanager_error import NoDbSessionAttachedError, NoInitialStateDefinedError
from statemanager.statemanager_error import NextStateNotDefinedError, NoStateDefinedError
from sqlalchemy.orm import sessionmaker
from statemanager.statemanager_domain import StateHistory, StateDefinition
from sqlalchemy import desc, and_
from datetime import datetime

__state_session_factory = None


def set_session_factory(sm: sessionmaker) -> None:
    global __state_session_factory
    __state_session_factory = sm


def _current_session() -> Session:
    if __state_session_factory is None:
        raise NoDbSessionAttachedError("DB Session is not attached, "
                                       "call initilaize in statemanager with db session factory")

    return scoped_session(__state_session_factory)


class StateManagerOutput:
    _rec_id = None
    _state_type = None
    _state_id = None
    _state_name = None
    _notes = None
    _userid = None
    _insert_ts = None

    def __init__(self, rec_id, state_type, state_id, state_name, notes, userid, insert_ts):
        self._rec_id = rec_id
        self._state_type = state_type
        self._state_id = state_id
        self._state_name = state_name
        self._notes = notes
        self._userid = userid
        self._insert_ts = insert_ts

    @property
    def rec_id(self):
        return self._rec_id

    @property
    def state_type(self):
        return self._state_type

    @property
    def state_id(self):
        return self._state_id

    @property
    def state_name(self):
        return self._state_name

    @property
    def notes(self):
        return self._notes

    @property
    def userid(self):
        return self._userid

    @property
    def insert_ts(self):
        return self._insert_ts

    def __repr__(self):
        return '<StateManagerOutput(rec_id=%s, state_type=%s, state_id=%s, ' \
               'state_name=%s, notes=%s, userid=%s, insert_ts=%s)>' % (
                   self._rec_id, self._state_type, self._state_id,
                   self._state_name, self._notes, self._userid, self._insert_ts
               )


def _get_all(state_type: str, rec_id: str) -> list:
    return _current_session().query(StateHistory, StateDefinition).filter(and_(
        and_(StateHistory.rec_id == rec_id, StateDefinition.state_type == state_type),
        StateHistory.state_id == StateDefinition.state_id)).order_by(
        desc(StateHistory.insert_ts)).all()


def get_state(state_type: str, rec_id: str) -> StateManagerOutput:
    history = _get_all(state_type, rec_id)

    if not history:
        return None

    latest_record = history[0]

    return StateManagerOutput(rec_id=latest_record.StateHistory.rec_id,
                              state_type=latest_record.StateDefinition.state_type,
                              state_id=latest_record.StateHistory.state_id,
                              state_name=latest_record.StateDefinition.state_name,
                              notes=latest_record.StateHistory.notes,
                              userid=latest_record.StateHistory.userid,
                              insert_ts=latest_record.StateHistory.insert_ts)


def get_history(state_type: str, rec_id: str) -> [StateManagerOutput]:
    history = _get_all(state_type, rec_id)

    if not history:
        return None

    all_records = []

    for row in history:
        all_records.append(StateManagerOutput(rec_id=row.StateHistory.rec_id,
                                              state_type=row.StateDefinition.state_type,
                                              state_id=row.StateHistory.state_id,
                                              state_name=row.StateDefinition.state_name,
                                              notes=row.StateHistory.notes,
                                              userid=row.StateHistory.userid,
                                              insert_ts=row.StateHistory.insert_ts)
                           )
    return all_records


def promote(state_type: str, rec_id: str, userid: str, notes: str) -> StateManagerOutput:
    current_state = get_state(state_type, rec_id)
    session = _current_session()
    if current_state is None:
        initial_state = session.query(StateDefinition).filter(and_(
            and_(StateDefinition.state_type == state_type, StateDefinition.next_state_id != None),
            StateDefinition.state_id.notin_(
                session.query(StateDefinition.next_state_id).filter(and_(
                    StateDefinition.state_type == state_type, StateDefinition.next_state_id != None))))).first()

        if initial_state is None:
            raise NoInitialStateDefinedError()

        session.add(StateHistory(rec_id=rec_id,
                                 state_id=initial_state.state_id,
                                 notes=notes,
                                 userid=userid,
                                 insert_ts=datetime.now()))
    else:
        current_state_definition = session.query(StateDefinition).filter(
            and_(StateDefinition.state_id == current_state.state_id,
                 StateDefinition.state_type == state_type)).first()

        # Is state defined or is it the last state?
        if current_state_definition is None:
            raise NoStateDefinedError()

        if current_state_definition.next_state_id is None:
            raise NextStateNotDefinedError()

        session.add(StateHistory(rec_id=rec_id,
                                 state_id=current_state_definition.next_state_id,
                                 notes=notes,
                                 userid=userid,
                                 insert_ts=datetime.now()))
    session.flush()
    session.commit()
    return get_state(state_type=state_type, rec_id=rec_id)


def demote(state_type: str, rec_id: str, userid: str, notes: str) -> StateManagerOutput:
    current_state = get_state(state_type, rec_id)

    if current_state is None:
        raise NoStateDefinedError()

    session = _current_session()

    all_possible_prior_state = session.query(StateDefinition).filter(
        and_(StateDefinition.state_type == state_type,
             StateDefinition.next_state_id == current_state.state_id)).all()

    if not all_possible_prior_state:
        raise NoStateDefinedError('No prior state to go to from StateDefinition')

    all_possible_state_ids = [prior_state.state_id for prior_state in all_possible_prior_state]

    prior_state_history = session.query(StateHistory).filter(
        and_(StateHistory.rec_id == rec_id, StateHistory.state_id.in_(all_possible_state_ids))).order_by(
        desc(StateHistory.insert_ts)).first()

    if not prior_state_history:
        raise NoStateDefinedError('No prior state to go to for the record')

    session.add(StateHistory(rec_id=rec_id,
                             state_id=prior_state_history.state_id,
                             notes=notes,
                             userid=userid,
                             insert_ts=datetime.now()))
    session.flush()
    session.commit()
    return get_state(state_type=state_type, rec_id=rec_id)