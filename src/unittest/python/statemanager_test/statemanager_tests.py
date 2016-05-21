import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os
from datetime import datetime
from statemanager.statemanager_error import NoWorkflowDefined


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

    def _initialize_tables(self):
        self.connection.execute(
            'insert into WORKFLOW_DEFINITION values(1,"TASK_APPROVAL", "N", null, null)'
        )
        self.connection.execute(
            'insert into STATE_DEFINITION values(1,1, "SUBMITTED",null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2,1, "VALIDATED",null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3,1, "APPROVED",null, null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4,1, "COMPLETED",null, null)')

        self.connection.execute('insert into WORKFLOW_STATE values(1,2)')
        self.connection.execute('insert into WORKFLOW_STATE values(2,3)')
        self.connection.execute('insert into WORKFLOW_STATE values(3,4)')
        self.connection.execute('insert into WORKFLOW_STATE values(4,null)')

        self.connection.execute(
            'insert into STATE_HISTORY values("1", 1, "submitted for approval", "USER1", '
            '"INITIAL", null, "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into STATE_HISTORY values("1", 2, "validated task", "USER2", '
            '"APPROVE" , null, "2016-01-01 00:05:00")')

    def test_workflow_latest_empty(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_RECORD')

        def caller():
            sm.state(item_id='1')

        self.assertRaises(NoWorkflowDefined, caller)

        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        self.assertEqual(sm.state(item_id='2'), None)

    def test_workflow_latest(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.state(item_id='1')

        self.assertEqual(sm_output.item_id, '1')
        self.assertEqual(sm_output.workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 2)
        self.assertEqual(sm_output.state_name, 'VALIDATED')
        self.assertEqual(sm_output.notes, 'validated task')
        self.assertEqual(sm_output.userid, 'USER2')
        self.assertEqual(sm_output.state_action, 'APPROVE')
        self.assertEqual(sm_output.insert_ts, datetime(2016, 1, 1, 0, 5, 0))

    def test_workflow_history_empty(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_RECORD')

        def caller():
            sm.history(item_id='1')

        self.assertRaises(NoWorkflowDefined, caller)

        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.history(item_id='2')
        self.assertEqual(sm_output, None)

    def test_workflow_history(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(workflow_type='TASK_APPROVAL')
        sm_output = sm.history(item_id='1')

        self.assertEqual(sm_output[0].item_id, '1')
        self.assertEqual(sm_output[0].workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output[0].state_id, 2)
        self.assertEqual(sm_output[0].state_name, 'VALIDATED')
        self.assertEqual(sm_output[0].notes, 'validated task')
        self.assertEqual(sm_output[0].userid, 'USER2')
        self.assertEqual(sm_output[0].state_action, 'APPROVE')
        self.assertEqual(sm_output[0].insert_ts, datetime(2016, 1, 1, 0, 5, 0))

        self.assertEqual(sm_output[1].item_id, '1')
        self.assertEqual(sm_output[1].workflow_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output[1].state_id, 1)
        self.assertEqual(sm_output[1].state_name, 'SUBMITTED')
        self.assertEqual(sm_output[1].notes, 'submitted for approval')
        self.assertEqual(sm_output[1].userid, 'USER1')
        self.assertEqual(sm_output[1].state_action, 'INITIAL')
        self.assertEqual(sm_output[1].insert_ts, datetime(2016, 1, 1, 0, 0, 0))


if __name__ == '__main__':
    unittest.main()
