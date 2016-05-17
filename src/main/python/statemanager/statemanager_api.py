from sqlalchemy.orm import sessionmaker
from statemanager import statemanager


def initialize(sm: sessionmaker) -> None:
    statemanager.set_session_factory(sm)


class StateManager:
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type

    def state(self, rec_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.workflow_type, rec_id)

    def history(self, rec_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.workflow_type, rec_id)

    def next(self, rec_id: str, userid: str, notes: str, criteria: str=None) -> statemanager.StateManagerOutput:
        return statemanager.next_state(self.workflow_type, rec_id=rec_id, userid=userid, notes=notes, criteria=criteria)

    def previous(self, rec_id: str, userid: str, notes: str) -> statemanager.StateManagerOutput:
        return statemanager.previous(self.workflow_type, rec_id=rec_id, userid=userid, notes=notes)
