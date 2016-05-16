import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os
from datetime import datetime


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
            'insert into STATE_DEFINITION values(1,"TASK_APPROVAL", "SUBMITTED",1)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2,"TASK_APPROVAL", "VALIDATED",2)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3,"TASK_APPROVAL", "APPROVED",3)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4,"TASK_APPROVAL", "COMPLETED",null)')

        self.connection.execute(
            'insert into STATE_HISTORY values("1", 1, "submitted for approval", "USER1", "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into STATE_HISTORY values("1", 2, "validated task", "USER2", "2016-01-01 00:05:00")')

    def test_workflow_latest_empty(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_RECORD')
        self.assertEqual(sm.state(rec_id='1'), None)
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        self.assertEqual(sm.state(rec_id='2'), None)

    def test_workflow_latest(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm_output = sm.state(rec_id='1')

        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.state_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 2)
        self.assertEqual(sm_output.state_name, 'VALIDATED')
        self.assertEqual(sm_output.notes, 'validated task')
        self.assertEqual(sm_output.userid, 'USER2')
        self.assertEqual(sm_output.insert_ts, datetime(2016, 1, 1, 0, 5, 0))

    def test_workflow_history_empty(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_RECORD')
        sm_output = sm.history(rec_id='1')
        self.assertEqual(sm_output, None)

        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm_output = sm.history(rec_id='2')
        self.assertEqual(sm_output, None)

    def test_workflow_history(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm_output = sm.history(rec_id='1')

        self.assertEqual(sm_output[0].rec_id, '1')
        self.assertEqual(sm_output[0].state_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output[0].state_id, 2)
        self.assertEqual(sm_output[0].state_name, 'VALIDATED')
        self.assertEqual(sm_output[0].notes, 'validated task')
        self.assertEqual(sm_output[0].userid, 'USER2')
        self.assertEqual(sm_output[0].insert_ts, datetime(2016, 1, 1, 0, 5, 0))

        self.assertEqual(sm_output[1].rec_id, '1')
        self.assertEqual(sm_output[1].state_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output[1].state_id, 1)
        self.assertEqual(sm_output[1].state_name, 'SUBMITTED')
        self.assertEqual(sm_output[1].notes, 'submitted for approval')
        self.assertEqual(sm_output[1].userid, 'USER1')
        self.assertEqual(sm_output[1].insert_ts, datetime(2016, 1, 1, 0, 0, 0))

if __name__ == '__main__':
    unittest.main()
