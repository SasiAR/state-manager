import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import api
import os
from statemanager.error import NoStateDefinedError, NoWorkflowDefined


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
            'insert into SM_WORKFLOW_DEFINITION values(1,"TASK_APPROVAL", "N", null, null)'
        )

        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(1, 1, "SUBMITTED", null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(2, 1, "VALIDATED",null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(3, 1, "APPROVED", null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(4, 1, "COMPLETED", null)')

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

    def test_no_item(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')

        def caller():
            sm.previous_state(item_type="TASKS", item_id='2', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoStateDefinedError, caller)

    def test_no_state_definition(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_MANAGE')

        def caller():
            sm.previous_state(item_type="TASKS", item_id='2', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoWorkflowDefined, caller)

    def test_sendback(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.previous_state(item_type="TASKS", item_id='1', userid='USER3', notes='disapprove to go ahead')
        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.state_action, 'REJECT')
        self.assertEqual(sm_output.notes, 'disapprove to go ahead')

    def test_sendback_failure(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm.previous_state(item_type="TASKS", item_id='1', userid='USER3', notes='disapprove to go ahead')

        def caller():
            sm.previous_state(item_type="TASKS", item_id='1', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoStateDefinedError, caller)

    def test_moveup_and_sendback(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.next_state(item_type="TASKS", item_id='1', userid='USER3', notes='approve one more level')
        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 3)
        self.assertEqual(sm_output.state_name, 'APPROVED')
        self.assertEqual(sm_output.state_action, 'APPROVE')
        self.assertEqual(sm_output.notes, 'approve one more level')
        sm_output = sm.previous_state(item_type="TASKS", item_id='1', userid='USER3', notes='disapprove to go ahead')
        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 2)
        self.assertEqual(sm_output.state_name, 'VALIDATED')
        self.assertEqual(sm_output.state_action, 'REJECT')
        self.assertEqual(sm_output.notes, 'disapprove to go ahead')
        sm_output = sm.previous_state(item_type="TASKS", item_id='1', userid='USER3', notes='disapprove to go ahead')
        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.state_action, 'REJECT')
        self.assertEqual(sm_output.notes, 'disapprove to go ahead')


if __name__ == '__main__':
    unittest.main()
