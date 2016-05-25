from sqlalchemy.orm import sessionmaker
from statemanager import statemanager
from statemanager import notifier, dao, version


def initialize(sm: sessionmaker, mailhost: str = None) -> None:
    dao.set_session_factory(sm)
    notifier.set_smtphost(mailhost)


class StateManager:
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type

    def state(self, item_id: str) -> statemanager.StateManagerOutput:
        return statemanager.get_state(self.workflow_type, item_id)

    def history(self, item_id: str) -> [statemanager.StateManagerOutput]:
        return statemanager.get_history(self.workflow_type, item_id)

    def add(self, item_id: str, userid: str, notes: str, criteria: str = None,
            user_subscription_notification: str = None, item_type: str = None) -> statemanager.StateManagerOutput:
        return self.moveup(item_id=item_id,
                           userid=userid,
                           notes=notes,
                           criteria=criteria,
                           user_subscription_notification=user_subscription_notification,
                           item_type=item_type)

    def moveup(self, item_id: str, userid: str, notes: str, criteria: str = None,
               user_subscription_notification: str = None, item_type: str = None) -> statemanager.StateManagerOutput:
        if item_type is not None:
            version.add_to_version(item_type=item_type, item_id=item_id)

        output = statemanager.moveup(self.workflow_type, item_id=item_id, userid=userid, notes=notes,
                                     criteria=criteria,
                                     user_subscription_notification=user_subscription_notification)
        self.notify_users(item_id=item_id)
        return output

    def sendback(self, item_id: str, userid: str, notes: str,
                 user_subscription_notification: str = None) -> statemanager.StateManagerOutput:
        output = statemanager.sendback(self.workflow_type, item_id=item_id,
                                       userid=userid, notes=notes,
                                       user_subscription_notification=user_subscription_notification)
        self.notify_users(item_id=item_id)
        return output

    def notify_users(self, item_id: str) -> bool:
        return notifier.notify_users(workflow_type=self.workflow_type, item_id=item_id)
