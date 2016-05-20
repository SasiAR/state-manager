import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os


class TestWorkflowState(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", echo=False)
        session_factory = sessionmaker(bind=engine)
        statemanager_api.initialize(session_factory)
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
            'insert into WORKFLOW_DEFINITION values(1,"TASK_APPROVAL", "N", null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(1, 1, "SUBMITTED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2, 1, "VALIDATED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3, 1, "APPROVED", null, "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4, 1, "COMPLETED","COMPLETE", "someone@fromsomewhere.com")')
        self.connection.execute(
            'insert into STATE_DEFINITION values(5, 1, "CLOSED","CLOSE", "someone@fromsomewhere.com")')

        self.connection.execute('insert into WORKFLOW_STATE values(1,2)')
        self.connection.execute('insert into WORKFLOW_STATE values(2,3)')
        self.connection.execute('insert into WORKFLOW_STATE values(3,4)')
        self.connection.execute('insert into WORKFLOW_STATE values(3,5)')
        self.connection.execute('insert into WORKFLOW_STATE values(4,5)')
        self.connection.execute('insert into WORKFLOW_STATE values(5,null)')

        self.connection.execute(
            'insert into STATE_HISTORY values("1", 1, "submitted for approval", "USER1", '
            '"INITIAL", null, "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into STATE_HISTORY values("1", 2, "validated task", "USER2", '
            '"APPROVE", null, "2016-01-01 00:05:00")')

    def test_notify(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type="TASK_APPROVAL")
        sm.notify_users(rec_id="1")

    def test_notify_pass(self):
        self._initialize_tables()
        self.connection.execute(
            'update WORKFLOW_DEFINITION set email_notification="Y", '
            ' email_subject="subject for notification",'
            ' email_content="content for email."'
            ' where workflow_id = 1')
        sm = statemanager_api.StateManager(workflow_type="TASK_APPROVAL")
        sm.notify_users(rec_id="1")


if __name__ == '__main__':
    unittest.main()
