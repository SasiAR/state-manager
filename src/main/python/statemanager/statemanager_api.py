from sqlalchemy.orm import sessionmaker
from statemanager import statemanager
from statemanager import statemanager_notifier


def initialize(sm: sessionmaker, mailhost: str=None) -> None:
    statemanager.set_session_factory(sm)
    statemanager_notifier.set_smtphost(mailhost)


class StateManager:
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type

    def state(self, item_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.workflow_type, item_id)

    def history(self, item_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.workflow_type, item_id)

    def next(self, item_id: str, userid: str, notes: str, criteria: str = None,
             user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.next_state(self.workflow_type, item_id=item_id, userid=userid, notes=notes,
                                         criteria=criteria,
                                         user_subscription_notification=user_subscription_notification)
        self.notify_users(item_id=item_id)
        return output

    def previous(self, item_id: str, userid: str, notes: str,
                 user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.previous(self.workflow_type, item_id=item_id,
                                       userid=userid, notes=notes,
                                       user_subscription_notification=user_subscription_notification)
        self.notify_users(item_id=item_id)
        return output

    def notify_users(self, item_id: str) -> bool:
        return statemanager_notifier.notify_users(workflow_type=self.workflow_type, item_id=item_id)
