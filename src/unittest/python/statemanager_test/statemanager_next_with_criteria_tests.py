import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from statemanager import statemanager_api
import os
from statemanager.statemanager_error import NoInitialStateDefinedError, NextStateNotDefinedError


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
            'insert into STATE_DEFINITION values(1,"TASK_APPROVAL", "SUBMITTED", null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(2,"TASK_APPROVAL", "VALIDATED", null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(3,"TASK_APPROVAL", "APPROVED", null)')
        self.connection.execute(
            'insert into STATE_DEFINITION values(4,"TASK_APPROVAL", "COMPLETED",null)')

        self.connection.execute('insert into STATE_WORKFLOW values(1,2)')
        self.connection.execute('insert into STATE_WORKFLOW values(2,3)')
        self.connection.execute('insert into STATE_WORKFLOW values(3,4)')
        self.connection.execute('insert into STATE_WORKFLOW values(4,null)')

        self.connection.execute(
            'insert into STATE_HISTORY values("1", 1, "submitted for approval", "USER1", "2016-01-01 00:00:00")')
        self.connection.execute(
            'insert into STATE_HISTORY values("1", 2, "validated task", "USER2", "2016-01-01 00:05:00")')
