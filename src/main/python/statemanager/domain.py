from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, String, Integer

Base = declarative_base()


class StateDefinition(Base):
    __tablename__ = 'SM_STATE_DEFINITION'

    state_id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer)
    state_name = Column(String)
    email_to = Column(String)

    def __repr__(self):
        return "<StateDefinition (state_id=%s, workflow_id=%s, state_name=%s, " \
               "email_to=%s)>" % (self.state_id,
                                  self.workflow_id,
                                  self.state_name,
                                  self.email_to)


class WorkflowState(Base):
    __tablename__ = 'SM_WORKFLOW_STATE'

    state_id = Column(Integer, primary_key=True)
    next_state_id = Column(Integer, primary_key=True)
    action = Column(String)

    def __repr__(self):
        return "<StateWorkflow(state_id=%s, next_state_id=%s, action=%s)>" % (
        self.state_id, self.next_state_id, self.action)


class StateHistory(Base):
    __tablename__ = 'SM_STATE_HISTORY'

    item_type = Column(String, primary_key=True)
    item_id = Column(String, primary_key=True)
    state_id = Column(Integer, primary_key=True)
    notes = Column(String)
    userid = Column(String, primary_key=True)
    state_action = Column(String)
    insert_ts = Column(DateTime, primary_key=True)
    user_subscription_notification = Column(String)

    def __repr__(self):
        return "<StateHistory (item_type,%s, item_id=%s, state_id=%s, notes=%s, userid=%s, " \
               "state_action=%s, insert_ts=%s)>" % (
                   self.item_type, self.item_id,
                   self.state_id, self.notes,
                   self.userid, self.state_action,
                   self.insert_ts
               )


class WorkflowDefinition(Base):
    __tablename__ = 'SM_WORKFLOW_DEFINITION'

    workflow_id = Column(Integer, primary_key=True)
    workflow_type = Column(String)
    email_notification = Column(String)
    email_subject = Column(String)
    email_content = Column(String)

    def __repr__(self):
        return "<WorkflowDefinition(workflow_id=%s, workflow_type=%s, email_notification=%s," \
               " email_subject=%s, email_content=%s" % (self.workflow_id,
                                                        self.workflow_type,
                                                        self.email_notification,
                                                        self.email_subject,
                                                        self.email_content
                                                        )


class ItemVersion(Base):
    __tablename__ = 'SM_VERSION'

    item_type = Column(String, primary_key=True)
    item_id = Column(String)
    version_number = Column(Integer, primary_key=True)
    created_ts = Column(DateTime)

    def __repr__(self):
        return "<Version(item_type=%s, item_id=%s, version_number=%s, created_ts=%s" % (self.item_type,
                                                                                        self.item_id,
                                                                                        self.version_number,
                                                                                        self.created_ts)
