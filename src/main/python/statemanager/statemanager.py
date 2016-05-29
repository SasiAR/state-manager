from statemanager.error import NoInitialStateDefinedError, NoWorkflowDefined
from statemanager.error import NextStateNotDefinedError, NoStateDefinedError
from statemanager.dao import current_session
from statemanager.domain import StateHistory, StateDefinition, WorkflowState, WorkflowDefinition
from sqlalchemy import desc, and_
from datetime import datetime
from enum import Enum


class StateAction(Enum):
    INITIAL = 1
    APPROVE = 2
    REJECT = 3


class StateManagerOutput:
    _item_type = None
    _item_id = None
    _workflow_type = None
    _state_id = None
    _state_name = None
    _notes = None
    _userid = None
    _insert_ts = None

    def __init__(self, item_type, item_id, workflow_type, state_id, state_name, notes, userid, state_action, insert_ts):
        self._item_id = item_type
        self._item_id = item_id
        self._workflow_type = workflow_type
        self._state_id = state_id
        self._state_name = state_name
        self._notes = notes
        self._userid = userid
        self._state_action = state_action
        self._insert_ts = insert_ts

    @property
    def item_type(self):
        return self._item_type

    @property
    def item_id(self):
        return self._item_id

    @property
    def workflow_type(self):
        return self._workflow_type

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
    def state_action(self):
        return self._state_action

    @property
    def insert_ts(self):
        return self._insert_ts

    def __repr__(self):
        return '<StateManagerOutput(item_type=%s, item_id=%s, workflow_type=%s, state_id=%s, ' \
               'state_name=%s, notes=%s, userid=%s, state_action=%s, insert_ts=%s)>' % (
                   self.item_type, self._item_id, self._workflow_type, self._state_id,
                   self._state_name, self._notes, self._userid, self._state_action, self._insert_ts
               )


def _get_workflow_definition(workflow_type: str) -> WorkflowDefinition:
    workflow_definition = current_session().query(WorkflowDefinition).filter(
        WorkflowDefinition.workflow_type == workflow_type).first()

    if workflow_definition is None:
        raise NoWorkflowDefined("No Workflow defined for type %s" % workflow_type)

    return workflow_definition


def _get_all(workflow_type: str, item_type: str, item_id: str) -> list:
    workflow_definition = _get_workflow_definition(workflow_type)
    return current_session().query(StateHistory, StateDefinition).filter(and_(and_(
        and_(StateHistory.item_id == item_id, StateDefinition.workflow_id == workflow_definition.workflow_id),
        StateHistory.state_id == StateDefinition.state_id), StateHistory.item_type == item_type)).order_by(
        desc(StateHistory.insert_ts)).all()


def get_state(workflow_type: str, item_type: str, item_id: str) -> StateManagerOutput:
    history = _get_all(workflow_type, item_type, item_id)

    if not history:
        return None

    latest_record = history[0]

    return StateManagerOutput(item_type=item_type,
                              item_id=latest_record.StateHistory.item_id,
                              workflow_type=workflow_type,
                              state_id=latest_record.StateHistory.state_id,
                              state_name=latest_record.StateDefinition.state_name,
                              notes=latest_record.StateHistory.notes,
                              userid=latest_record.StateHistory.userid,
                              state_action=latest_record.StateHistory.state_action,
                              insert_ts=latest_record.StateHistory.insert_ts)


def get_history(workflow_type: str, item_type: str, item_id: str) -> [StateManagerOutput]:
    history = _get_all(workflow_type, item_type, item_id)

    if not history:
        return None

    all_records = []

    for row in history:
        all_records.append(StateManagerOutput(item_type=item_type,
                                              item_id=row.StateHistory.item_id,
                                              workflow_type=workflow_type,
                                              state_id=row.StateHistory.state_id,
                                              state_name=row.StateDefinition.state_name,
                                              notes=row.StateHistory.notes,
                                              userid=row.StateHistory.userid,
                                              state_action=row.StateHistory.state_action,
                                              insert_ts=row.StateHistory.insert_ts)
                           )
    return all_records


def moveup(workflow_type: str, item_type: str, item_id: str, criteria: str, userid: str, notes: str,
           user_subscription_notification: str) -> StateManagerOutput:
    workflow_definition = _get_workflow_definition(workflow_type)
    current_state = get_state(workflow_type, item_type, item_id)
    session = current_session()
    if current_state is None:

        initial_state = session.query(StateDefinition, WorkflowState).filter(and_(
            and_(StateDefinition.workflow_id == workflow_definition.workflow_id,
                 WorkflowState.state_id == StateDefinition.state_id),
            StateDefinition.state_id.notin_(session.query(WorkflowState.next_state_id).filter(
                WorkflowState.next_state_id != None)
            ))).first()

        if initial_state is None:
            raise NoInitialStateDefinedError()

        session.add(StateHistory(item_type=item_type,
                                 item_id=item_id,
                                 state_id=initial_state.StateDefinition.state_id,
                                 notes=notes,
                                 userid=userid,
                                 state_action=StateAction.INITIAL.name,
                                 user_subscription_notification=user_subscription_notification,
                                 insert_ts=datetime.now()))
    else:
        next_state_definitions = session.query(StateDefinition, WorkflowState).filter(
            and_(StateDefinition.state_id == WorkflowState.state_id,
                 and_(StateDefinition.state_id.in_(session.query(WorkflowState.next_state_id).filter(
                     WorkflowState.state_id == current_state.state_id)),
                     StateDefinition.workflow_id == workflow_definition.workflow_id))).all()

        # Is state defined or is it the last state?
        if not next_state_definitions:
            raise NextStateNotDefinedError()

        next_state_definition = next_state_definitions[0]
        if criteria is not None and next_state_definitions:
            next_state_definition = next(iter(
                [state for state in next_state_definitions if state.StateDefinition.criteria == criteria]))

        if next_state_definition is None:
            raise NextStateNotDefinedError()

        session.add(StateHistory(item_type=item_type,
                                 item_id=item_id,
                                 state_id=next_state_definition.WorkflowState.state_id,
                                 notes=notes,
                                 userid=userid,
                                 state_action=StateAction.APPROVE.name,
                                 user_subscription_notification=user_subscription_notification,
                                 insert_ts=datetime.now()))
    session.flush()
    return get_state(workflow_type=workflow_type, item_type=item_type, item_id=item_id)


def sendback(workflow_type: str, item_type: str, item_id: str, userid: str, notes: str,
             user_subscription_notification: str) -> StateManagerOutput:
    workflow_definition = _get_workflow_definition(workflow_type)
    current_state = get_state(workflow_type, item_type, item_id)

    if current_state is None:
        raise NoStateDefinedError()

    session = current_session()

    all_possible_prior_state = session.query(StateDefinition, WorkflowState).filter(
        and_(WorkflowState.state_id == StateDefinition.state_id,
             and_(StateDefinition.workflow_id == workflow_definition.workflow_id,
                  WorkflowState.next_state_id == current_state.state_id))).all()

    if not all_possible_prior_state:
        raise NoStateDefinedError('No prior state to go to from StateDefinition')

    all_possible_state_ids = [prior_state.StateDefinition.state_id for prior_state in all_possible_prior_state]

    prior_state_history = session.query(StateHistory).filter(and_(
        and_(StateHistory.item_id == item_id, StateHistory.state_id.in_(all_possible_state_ids)),
        StateHistory.item_type == item_type)).order_by(
        desc(StateHistory.insert_ts)).first()

    if not prior_state_history:
        raise NoStateDefinedError('No prior state to go to for the record')

    session.add(StateHistory(item_type=item_type,
                             item_id=item_id,
                             state_id=prior_state_history.state_id,
                             notes=notes,
                             userid=userid,
                             state_action=StateAction.REJECT.name,
                             user_subscription_notification=user_subscription_notification,
                             insert_ts=datetime.now()))
    session.flush()
    return get_state(workflow_type=workflow_type, item_type=item_type, item_id=item_id)
