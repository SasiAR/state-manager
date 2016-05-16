from sqlalchemy.orm import sessionmaker
from statemanager import statemanager


def initialize(sm: sessionmaker) -> None:
    statemanager.set_session_factory(sm)


class StateManager:
    def __init__(self, state_type: str):
        self.state_type = state_type

    def state(self, rec_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.state_type, rec_id)

    def history(self, rec_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.state_type, rec_id)

    def promote(self, rec_id: str, userid: str, notes: str) -> statemanager.StateManagerOutput:
        return statemanager.promote(self.state_type, rec_id=rec_id, userid=userid, notes=notes)

    def demote(self, rec_id: str, userid: str, notes: str) -> statemanager.StateManagerOutput:
        return statemanager.demote(self.state_type, rec_id=rec_id, userid=userid, notes=notes)
