import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import api, notifier
import os
from email.mime.text import MIMEText


class TestWorkflowState(unittest.TestCase):
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
            'insert into SM_STATE_DEFINITION values(1, 1, "SUBMITTED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(2, 1, "VALIDATED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(3, 1, "APPROVED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(4, 1, "COMPLETED","COMPLETE", "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(5, 1, "CLOSED","CLOSE", "someone@fromsomewhere.com")')

        self.connection.execute('insert into SM_WORKFLOW_STATE values(1,2)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(2,3)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,4)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,5)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(4,5)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(5,null)')

        self.connection.execute(
            'insert into SM_STATE_HISTORY values("1", 1, "submitted for approval", "USER1", '
            '"INITIAL", null, "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into SM_STATE_HISTORY values("1", 2, "validated task", "USER2", '
            '"APPROVE", null, "2016-01-01 00:05:00")')

    def test_notify(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type="TASK_APPROVAL")
        self.assertFalse(sm.notify_users(item_id="1"))

    def test_notify_pass(self):
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
        self.assertTrue(sm.notify_users(item_id="1"))

        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual([], msg_result._headers[5][1])
        self.assertEqual("content for email. The state was changed to VALIDATED with notes - validated task",
                         msg_result._payload)

    def test_notify_pass_sendback(self):
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
        sm.moveup(item_id='1', userid='USER3', notes='approved to got the next stage')

        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual([], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to APPROVED with notes - approved to got the next stage",
                         msg_result._payload)

    def test_notify_pass_sendback_subsription(self):
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
        sm.sendback(item_id='1', userid='USER3', notes='reject the approval request',
                    user_subscription_notification='user3@fromsomewhere.com')

        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to SUBMITTED with notes - reject the approval request",
                         msg_result._payload)

    def test_notify_pass_moveup_subscription(self):
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
        sm.moveup(item_id='1', userid='USER3', notes='approved to got the next stage',
                  user_subscription_notification='user3@fromsomewhere.com')
        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to APPROVED with notes - approved to got the next stage",
                         msg_result._payload)

        sm.moveup(item_id='1', userid='USER4', notes='approved to got the next stage',
                  user_subscription_notification='user4@fromsomewhere.com')

        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com", "user4@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to COMPLETED with notes - approved to got the next stage",
                         msg_result._payload)

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
        sm.moveup(item_id='1', userid='USER3', notes='approved to got the next stage',
                  user_subscription_notification='user3@fromsomewhere.com')
        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to APPROVED with notes - approved to got the next stage",
                         msg_result._payload)

        sm.moveup(item_id='1', userid='USER3', notes='approved to got the next stage',
                  user_subscription_notification='user3@fromsomewhere.com')

        self.assertEqual(["someone@fromsomewhere.com"], msg_result._headers[4][1])
        self.assertEqual(["user3@fromsomewhere.com"], msg_result._headers[5][1])
        self.assertEqual("content for email. "
                         "The state was changed to COMPLETED with notes - approved to got the next stage",
                         msg_result._payload)

if __name__ == '__main__':
    unittest.main()
