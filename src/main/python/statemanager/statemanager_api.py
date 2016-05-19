from sqlalchemy.orm import sessionmaker
from statemanager import statemanager
from statemanager import statemanager_notifier


def initialize(sm: sessionmaker) -> None:
    statemanager.set_session_factory(sm)


class StateManager:
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type

    def state(self, rec_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.workflow_type, rec_id)

    def history(self, rec_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.workflow_type, rec_id)

    def next(self, rec_id: str, userid: str, notes: str, criteria: str = None,
             user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.next_state(self.workflow_type, rec_id=rec_id, userid=userid, notes=notes,
                                         criteria=criteria,
                                         user_subscription_notification=user_subscription_notification)
        self.notify_users(rec_id=rec_id)
        return output

    def previous(self, rec_id: str, userid: str, notes: str) -> statemanager.StateManagerOutput:
        output = statemanager.previous(self.workflow_type, rec_id=rec_id, userid=userid, notes=notes)
        self.notify_users(rec_id=rec_id)
        return output

    def notify_users(self, rec_id: str) -> None:
        statemanager_notifier.notify_users(workflow_type=self.workflow_type, rec_id=rec_id)
