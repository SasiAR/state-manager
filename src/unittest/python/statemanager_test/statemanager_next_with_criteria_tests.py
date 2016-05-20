import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os
from statemanager.statemanager_error import NextStateNotDefinedError


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
            'insert into STATE_DEFINITION values(1, 1, "SUBMITTED", null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2, 1, "VALIDATED", null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3, 1, "APPROVED", null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4, 1, "COMPLETED","COMPLETE", null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(5, 1, "CLOSED","CLOSE", null)')

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

    def test_next_with_criteria(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm.next(rec_id='1', userid='USER3', notes='approved to got the next stage')
        sm_output = sm.next(rec_id='1', userid='USER3', notes='close the task', criteria='CLOSE')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 5)
        self.assertEqual(sm_output.state_name, 'CLOSED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'close the task')

    def test_next_with_criteria2(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm.next(rec_id='1', userid='USER3', notes='approved to got the next stage')
        sm_output = sm.next(rec_id='1', userid='USER3', notes='complete the task', criteria='COMPLETE')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 4)
        self.assertEqual(sm_output.state_name, 'COMPLETED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'complete the task')
        sm_output = sm.next(rec_id='1', userid='USER3', notes='close the task', criteria='CLOSE')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 5)
        self.assertEqual(sm_output.state_name, 'CLOSED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'close the task')

    def test_next_with_criteria_failure(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm.next(rec_id='1', userid='USER3', notes='approved to got the next stage')
        sm.next(rec_id='1', userid='USER3', notes='complete the task')
        sm_output = sm.next(rec_id='1', userid='USER3', notes='close the task')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 5)
        self.assertEqual(sm_output.state_name, 'CLOSED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'close the task')

    def test_next_with_criteria_failure2(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm.next(rec_id='1', userid='USER3', notes='approved to got the next stage')
        sm.next(rec_id='1', userid='USER3', notes='complete the task')
        sm.next(rec_id='1', userid='USER3', notes='close the task')

        def caller():
            sm.next(rec_id='1', userid='USER3', notes='close the task')

        self.assertRaises(NextStateNotDefinedError, caller)


if __name__ == '__main__':
    unittest.main()
