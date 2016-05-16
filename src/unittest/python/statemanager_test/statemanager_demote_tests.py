import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os
from statemanager.statemanager_error import NoStateDefinedError


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
            'insert into STATE_DEFINITION values(1,"TASK_APPROVAL", "SUBMITTED",2)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2,"TASK_APPROVAL", "VALIDATED",3)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3,"TASK_APPROVAL", "APPROVED",4)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4,"TASK_APPROVAL", "COMPLETED",null)')

        self.connection.execute(
            'insert into STATE_HISTORY values("1", 1, "submitted for approval", "USER1", "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into STATE_HISTORY values("1", 2, "validated task", "USER2", "2016-01-01 00:05:00")')

    def test_no_rec(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')

        def caller():
            sm.demote(rec_id='2', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoStateDefinedError, caller)

    def test_no_state_definition(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_MANAGE')

        def caller():
            sm.demote(rec_id='2', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoStateDefinedError, caller)

    def test_demote(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm_output = sm.demote(rec_id='1', userid='USER3', notes='disapprove to go ahead')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.state_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.notes, 'disapprove to go ahead')

    def test_demote_failure(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm.demote(rec_id='1', userid='USER3', notes='disapprove to go ahead')

        def caller():
            sm.demote(rec_id='1', userid='USER3', notes='disapprove to go ahead')

        self.assertRaises(NoStateDefinedError, caller)

    def test_promote_and_demote(self):
        self._initialize_tables()
        sm = statemanager_api.StateManager(state_type='TASK_APPROVAL')
        sm.promote(rec_id='1', userid='USER3', notes='approve one more level')
        sm.demote(rec_id='1', userid='USER3', notes='disapprove to go ahead')
        sm_output = sm.demote(rec_id='1', userid='USER3', notes='disapprove to go ahead')
        self.assertEqual(sm_output.rec_id, '1')
        self.assertEqual(sm_output.state_type, 'TASK_APPROVAL')
        self.assertEqual(sm_output.state_id, 1)
        self.assertEqual(sm_output.state_name, 'SUBMITTED')
        self.assertEqual(sm_output.notes, 'disapprove to go ahead')

if __name__ == '__main__':
    unittest.main()
