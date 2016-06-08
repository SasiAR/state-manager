import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import api, notifier
import os
from email.mime.text import MIMEText


class TestWorkflowNotification(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", echo=False)
        session_factory = sessionmaker(bind=engine)
        api.initialize(session_factory)
        ddl_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                '../../../../resources/database-schema/required_tables.sql')
        ddls = ""
        with open(ddl_file) as in_file:
            ddls += in_file.read()
        ddls = ddls.split(';')

        with engine.connect() as connection:
            for ddl in ddls:
                connection.execute(ddl)

        self.connection = engine.connect()
        self.session_factory = session_factory

    def _initialize_tables(self):
        self.connection.execute(
            'insert into SM_WORKFLOW_DEFINITION values(1,"TASK_APPROVAL", "N", null, null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(1, 1, "SUBMITTED", "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(2, 1, "VALIDATED", "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(3, 1, "APPROVED", "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(4, 1, "COMPLETED","someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(5, 1, "CLOSED", "someone@fromsomewhere.com")')

        self.connection.execute('insert into SM_WORKFLOW_STATE values(1,2, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(2,3, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,4, "COMPLETE")')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,5, "CLOSE")')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(4,5, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(5,null, null)')

        self.connection.execute(
            'insert into SM_STATE_HISTORY values("TASKS", "1", 1, "submitted for approval", "USER1", '
            '"INITIAL", null, "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into SM_STATE_HISTORY values("TASKS", "1", 2, "validated task", "USER2", '
            '"APPROVE", null, "2016-01-01 00:05:00")')

    def test_notify_pass_moveup_nultiple_subscription(self):
        def mock_notification(msg: MIMEText):
            global msg_result
            msg_result = msg

        notifier._send_notification = mock_notification
        self._initialize_tables()
        self.connection.execute(
            'update SM_WORKFLOW_DEFINITION set email_notification="Y", '
            ' email_subject="subject for notification",'
            ' email_content="content for email."'
            ' where workflow_id = 1')
        sm = api.StateManager(workflow_type="TASK_APPROVAL")
        sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage',
                      user_subscription_notification='user3@fromsomewhere.com')
        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to APPROVED with notes - approved to got the next stage",
                         msg_result._payload)

        sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage',
                      user_subscription_notification='user3@fromsomewhere.com')
        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to COMPLETED with notes - approved to got the next stage",
                         msg_result._payload)

if __name__ == '__main__':
    unittest.main()
