from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, String, Integer

Base = declarative_base()


class StateDefinition(Base):
    __tablename__ = 'STATE_DEFINITION'

    state_id = Column(Integer, primary_key=True)
    state_type = Column(String)
    state_name = Column(String)
    next_state_id = Column(Integer)

    def __repr__(self):
        return "<StateDefinition (state_id=%s, state_type=%s, state_name=%s, next_state_id=%s" % (self.state_id,
                                                                                                  self.state_type,
                                                                                                  self.state_name,
                                                                                                  self.next_state_id)


class StateHistory(Base):
    __tablename__ = 'STATE_HISTORY'

    rec_id = Column(String, primary_key=True)
    state_id = Column(Integer, primary_key=True)
    notes = Column(String)
    userid = Column(String, primary_key=True)
    insert_ts = Column(DateTime, primary_key=True)

    def __repr__(self):
        return "<StateHistory (rec_id=%s, state_id=%s, notes=%s, userid=%s, insert_ts=%s" % (
            self.rec_id, self.state_id, self.notes, self.userid, self.insert_ts
        )
