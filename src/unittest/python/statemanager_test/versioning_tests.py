import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import api
import os


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
            'insert into SM_STATE_DEFINITION values(1,1, "SUBMITTED", null, null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(2,1, "VALIDATED", null, null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(3,1, "APPROVED", null, null)')
        self.connection.execute(
            'insert into SM_STATE_DEFINITION values(4,1, "COMPLETED",null, null)')

        self.connection.execute('insert into SM_WORKFLOW_STATE values(1,2)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(2,3)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(3,4)')
        self.connection.execute('insert into SM_WORKFLOW_STATE values(4,null)')

    def test_version_no_add(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm.add(item_type='TASKS', item_id='1', userid='USER1', notes='approved to got the next stage')
        result = self.connection.execute('select * from sm_version').fetchall()
        self.assertEqual([], result)

    def test_version_add(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm.add_with_version(item_id='1', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
        result = self.connection.execute('select * from sm_version').fetchall()
        self.assertEqual(1, len(result))
        self.assertEqual('TASKS', result[0][0])
        self.assertEqual('1', result[0][1])
        self.assertEqual(1, result[0][2])

    # def test_version_add_mutiple(self):
    #     self._initialize_tables()
    #     sm = api.StateManager(workflow_type='TASK_APPROVAL')
    #     sm.add_with_version(item_id='1', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
    #     sm.moveup(item_id='1', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
    #     result = self.connection.execute('select * from sm_version').fetchall()
    #     self.assertEqual(1, len(result))
    #     self.assertEqual('TASKS', result[0][0])
    #     self.assertEqual('1', result[0][1])
    #     self.assertEqual(1, result[0][2])

    def test_add_mutiple_version(self):
        self._initialize_tables()
        sm = api.StateManager(workflow_type='TASK_APPROVAL')
        sm.add_with_version(item_id='1', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
        sm.moveup(item_id='1', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
        sm.add_with_version(item_id='2', userid='USER1', notes='approved to got the next stage', item_type='TASKS')
        result = self.connection.execute('select * from sm_version').fetchall()
        self.assertEqual(2, len(result))
        self.assertEqual('TASKS', result[0][0])
        self.assertEqual('1', result[0][1])
        self.assertEqual(1, result[0][2])
        self.assertEqual('TASKS', result[1][0])
        self.assertEqual('2', result[1][1])
        self.assertEqual(2, result[1][2])