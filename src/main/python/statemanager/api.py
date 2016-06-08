from sqlalchemy.orm import sessionmaker
from statemanager import statemanager
from statemanager import notifier, dao, version


def initialize(sm: sessionmaker, mailhost: str = None) -> None:
    dao.set_session_factory(sm)
    notifier.set_smtphost(mailhost)


class StateManager:
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type

    def state(self, item_type: str, item_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.workflow_type, item_type, item_id)

    def history(self, item_type: str, item_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.workflow_type, item_type, item_id)

    def add(self, item_id: str, userid: str, notes: str, item_type: str, action: str = None,
            user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        return self.next_state(item_id=item_id,
                               userid=userid,
                               notes=notes,
                               action=action,
                               user_subscription_notification=user_subscription_notification,
                               item_type=item_type)

    def add_with_version(self, item_id: str, userid: str, notes: str, item_type: str, action: str = None,
                         user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        version.add_to_version(item_type=item_type, item_id=item_id)

        return self.next_state(item_id=item_id,
                               userid=userid,
                               notes=notes,
                               action=action,
                               user_subscription_notification=user_subscription_notification,
                               item_type=item_type)

    def next_state(self, item_id: str, userid: str, notes: str, item_type: str, action: str = None,
                   user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.next_state(self.workflow_type, item_id=item_id, userid=userid, notes=notes,
                                         action=action, item_type=item_type,
                                         user_subscription_notification=user_subscription_notification)
        self.notify_users(item_type=item_type, item_id=item_id)
        return output

    def previous_state(self, item_type: str, item_id: str, userid: str, notes: str,
                       user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.previous_state(self.workflow_type, item_type=item_type, item_id=item_id,
                                             userid=userid, notes=notes,
                                             user_subscription_notification=user_subscription_notification)
        self.notify_users(item_type=item_type, item_id=item_id)
        return output

    def notify_users(self, item_type: str, item_id: str) -> bool:
        return notifier.notify_users(workflow_type=self.workflow_type, item_type=item_type, item_id=item_id)
