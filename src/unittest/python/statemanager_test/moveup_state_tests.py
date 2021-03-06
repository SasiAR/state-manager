import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import api
import os
from statemanager.error import NextStateNotDefinedError, NoWorkflowDefined


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
            'insert into SM_STATE_DEFINITION values(1,1, "SUBMITTED", null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(2,1, "VALIDATED", null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(3,1, "APPROVED", null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(4,1, "COMPLETED", null)')

        self.connection.execute('insert into SM_WORKFLOW_STATE values(1,2, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(2,3, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,4, null)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(4,null, null)')

        self.connection.execute(
            'insert into SM_STATE_HISTORY values("TASKS", "1", 1, "submitted for approval", "USER1", '
            '"INITIAL", null, "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into SM_STATE_HISTORY values("TASKS", "1", 2, "validated task", "USER2", '
            '"APPROVE", null, "2016-01-01 00:05:00")')

    def test_moveup_state(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage')
        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 3)
        self.assertEqual(sm_output.state_name, 'APPROVED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'approved to got the next stage')

    def test_add(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.add(item_type="TASKS", item_id='2', userid='USER3', notes='submit my task for initial state')
        self.assertEqual(sm_output.item_id, '2')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.state_action, "INITIAL")
        self.assertEqual(sm_output.notes, 'submit my task for initial state')

    def test_add_and_moveup(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.add(item_type="TASKS", item_id='2', userid='USER3', notes='submit my task for initial state')
        self.assertEqual(sm_output.item_id, '2')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.state_action, "INITIAL")
        self.assertEqual(sm_output.notes, 'submit my task for initial state')
        sm_output = sm.next_state(item_type="TASKS", item_id='2', userid='USER4', notes='validate task')
        self.assertEqual(sm_output.item_id, '2')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 2)
        self.assertEqual(sm_output.state_name, 'VALIDATED')
        self.assertEqual(sm_output.state_action, "APPROVE")
        self.assertEqual(sm_output.notes, 'validate task')

    def test_no_state(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_MANAGE')

        def caller():
            sm.next_state(item_type="TASKS", item_id='3', userid='USER3', notes='submit my task for initial state')

        self.assertRaises(NoWorkflowDefined, caller)

    def test_final_state(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage')
        sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage')

        def caller():
            sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approved to got the next stage')

        self.assertRaises(NextStateNotDefinedError, caller)


if __name__ == '__main__':
    unittest.main()
